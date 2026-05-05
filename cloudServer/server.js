// SecureChat Node Ver
// APR 26: Porting from Python. Python time is not supported, so new time functions created.

//debug MAY 3., 2026 mor
console.log("VERSION CHECK: CLEAN MYSQL FIX 1");
console.log("MYSQL DECLARATION TEST");
console.log("FILE LOADED AT:", __filename);

//Handling BB storage
//import { S3Client, PutObjectCommand, GetObjectCommand } from "@aws-sdk/client-s3";
//import { getSignedUrl } from "@aws-sdk/s3-request-presigner";


//const BUCKET = "SecureChatGrp3-Files";use direct
/* removed MAY 3 MOR
require("dotenv").config(); //use dotenv to hide my database credential, even in testing process, APR 30 EVE
console.log("env debug temp code");
console.log("DB_HOST =", process.env.DB_HOST);
console.log("DB_USER =", process.env.DB_USER);
console.log("DB_NAME =", process.env.DB_NAME);
console.log("DB_PORT =", process.env.DB_PORT);
console.log("--------------");*/

//handle Backblaze
//const { S3Client, PutObjectCommand } = require("@aws-sdk/client-s3"); //start using Backblaze, MAY 2 MOR
const { S3Client, PutObjectCommand, GetObjectCommand } = require("@aws-sdk/client-s3"); //FIXED, MAY 2 MOR
const { getSignedUrl } = require("@aws-sdk/s3-request-presigner");

const s3 = new S3Client({
  region: "us-west-004",
  endpoint: "https://s3.us-west-004.backblazeb2.com",
  credentials: {
    accessKeyId: process.env.B2_KEY_ID,
    secretAccessKey: process.env.B2_APP_KEY
  }
});

const WebSocket = require("ws");
const fs = require("fs");
const path = require("path");
const bcrypt = require("bcrypt");
const crypto = require("crypto");
const glob = require("glob"); // MAR 15 EVE: To fix the numbering session error after TURN OFF Server
const mysql = require("mysql2"); //APR 30 EVE: To test Database on Infinity free, using mysql2 library

//EXPRES update, MAY 2 MOR
const express = require("express");
const app = express();
app.use(express.json({ limit: "23mb" }));

const server = require("http").createServer(app)

//handle mySQL //eliminated MAY 3, MOR
/*const db = mysql.createPool({
    host: process.env.DB_HOST,
    user: process.env.DB_USER,
    password: process.env.DB_PASSWORD,
    database: process.env.DB_NAME,
    port: process.env.DB_PORT || 3306
});*/

//to match with Railway URL settting, MAY 3 MOR
//const db = mysql.createPool(process.env.MYSQL_PUBLIC_URL); failed to deploy
if (!process.env.MYSQL_PUBLIC_URL) {
    throw new Error("MYSQL_PUBLIC_URL is missing in environment variables");
}

//const db = mysql.createPool(process.env.MYSQL_PUBLIC_URL);


const dbUrl = new URL(process.env.MYSQL_PUBLIC_URL); 
const db = mysql.createPool({ host: dbUrl.hostname, user: dbUrl.username, password: dbUrl.password, database: dbUrl.pathname.replace(/^\/+/, ""), port: dbUrl.port || 3306 });
console.log("DB URL loaded:", !!process.env.MYSQL_PUBLIC_URL);


//let registered_users = {}; remove because local storage now on MySQL
//let clients_connected_dict = {}; // store name of client REMOVE APR 30 MOR
let clients_connected_dict = new Map(); //test MAP for more stable access and connections

let clients_p_keys = {};
let last_pong = {}; // tracking last pong message
let active_chat_pairs = new Set();
let chat_sessions = {}; // MAR 10 eve: needed for the new chatfile system
let aes_session_keys = {};
let heartbeat_failures = {};
let failed_attempts_dict = {}; // MAR 7: Block login
let user_timestamp_dict = {}; // rate limit
let public_key_fingerprints = {}; //MAY 1, this one to update the hashing system

const mess_limit = 5;
const time_range = 8;

const max_attempts_allowed = 3;
const block_login_time = 10;
const session_tokens = {}; //add session token ID. MAY 1 EVE

//testBB
async function testBB() {
    console.log("Bb is OK:", !!s3);
}

testBB();

//Using BackBlaze [BB]
async function BBupload(filename, buffer, mimetype) {
    const key = `securechat/${Date.now()}_${filename}`;

    await s3.send(new PutObjectCommand({
        Bucket: process.env.B2_BUCKET,
        Key: key,
        Body: buffer,
        ContentType: mimetype
    }));

    return `https://f003.backblazeb2.com/file/${process.env.B2_BUCKET}/${key}`;
}

//Add new fuction to record directly into databased MAY 1 EVE
async function saveMess(sender, receiver, content, type, filename = null, size = null) {
    try {
        await db.promise().query(
            `INSERT INTO messages 
            (sender, receiver, content, type, filename, size, created_at)
            VALUES (?, ?, ?, ?, ?, ?, NOW())`,
            [sender, receiver, content, type, filename, size]
        );
    } catch (err) {
        console.log("Database save error:", err);
    }
}

//Time utils
function getTimeNowSeconds() {
    return Date.now() / 1000;
}

function getTimeString() {
    return new Date().toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit"
    });
}

//Log system
function write_system_log(message) {
    const sys_log_line = `[SYSTEM] ${message}`;
    fs.appendFileSync("chat_logs/system_log.txt", sys_log_line + "\n");
}

//SESSION SYSTEM
function get_current_sessionNo(user1, user2) {
    const users_pair = [user1, user2].sort();
    const pair_key = users_pair.join("_");
    const pattern = `chat_logs/${users_pair[0]}_${users_pair[1]}_session*.txt`;

    const files = glob.sync(pattern);
    if (files.length === 0) {
        chat_sessions[pair_key] = 1;
        return 1;
    }

    const session_numbers = files.map(file => {
        const match = file.match(/session(\d+)\.txt/);
        return match ? parseInt(match[1]) : 0;
    });

    const last_session = Math.max(...session_numbers);
    chat_sessions[pair_key] = last_session;
    return last_session;
}

function start_new_session(user1, user2) {
    const users_pair = [user1, user2].sort();
    const pair_key = users_pair.join("_");

    if (!chat_sessions[pair_key]) {
        get_current_sessionNo(user1, user2);
    }

    chat_sessions[pair_key] = (chat_sessions[pair_key] || 0) + 1;
    return chat_sessions[pair_key];
}

function write_mess_to_log(user1, user2, chat_message) {
    const users_pair = [user1, user2].sort();
    const pair_key = users_pair.join("_");

    if (!chat_sessions[pair_key]) chat_sessions[pair_key] = 1;

    const session = chat_sessions[pair_key];
    const chat_log_record = `chat_logs/${users_pair[0]}_${users_pair[1]}_session${session}.txt`;
    fs.appendFileSync(chat_log_record, chat_message + "\n", { encoding: "utf8" });
}

//AUTH
function hash_pass(plain_pass) {
    return bcrypt.hashSync(plain_pass, 10);
}

function check_pass(plain_pass, hashed) {
    return bcrypt.compareSync(plain_pass, hashed);
}

function validate_password(password) {
    if (password.length < 8) return [false, "8 characters password is required"];
    if (!/[A-Z]/.test(password)) return [false, "Uppercase letter required"];
    if (!/[a-z]/.test(password)) return [false, "Lowercase letter required"];
    if (!/[0-9]/.test(password)) return [false, "Number required"];
    return [true, "OK"];
}

//RATE LIMIT
function allowed_to_send(username) {
    const now = getTimeNowSeconds();
    if (!user_timestamp_dict[username]) user_timestamp_dict[username] = [];

    user_timestamp_dict[username] =
        user_timestamp_dict[username].filter(t => now - t < time_range);

    if (user_timestamp_dict[username].length >= mess_limit) return false;

    user_timestamp_dict[username].push(now);
    return true;
}

//LOGIN PROTECTION
function allowed_to_try_login(username) {
    const now = getTimeNowSeconds();
    if (!failed_attempts_dict[username]) return true;

    const [count, last] = failed_attempts_dict[username];
    if (count < max_attempts_allowed) return true;

    if (now - last > block_login_time) {
        delete failed_attempts_dict[username];
        user_timestamp_dict[username] = [];
        return true;
    }
    return false;
}

function record_failed_login(username) {
    const now = getTimeNowSeconds();
    if (!failed_attempts_dict[username]) {
        failed_attempts_dict[username] = [1, now];
    } else {
        failed_attempts_dict[username][0]++;
        failed_attempts_dict[username][1] = now;
    }
}

//May 1, same logic, make a new function to handle ws.on("error") and ws.on("close").
function removeClient(ws) {
    //add the prevention of double-removable
    if (!ws || ws._removed) 
        return;
    ws._removed = true;

    const user = clients_connected_dict.get(ws);
    clients_connected_dict.delete(ws);

    if (user) {
        wss.clients.forEach(c => {
            if (c.readyState === WebSocket.OPEN) {
                c.send(JSON.stringify({
                    type: "user_left",
                    username: user
                }));
            }
        });
    }
}

//USER STORAGE
/*
function load_users() {
    try {
        //return JSON.parse(fs.readFileSync("users.json", "utf8"));
        
    } catch {
        return {};
    }
}*/

/*In use upto APR 30 EVE, moved to use mysql
function load_users() {
    try {
        if (!fs.existsSync("users.json")) 
            return {};
        return JSON.parse(fs.readFileSync("users.json", "utf8"));
    } catch (err) {
        console.log("User loading error:", err);
        return {};
    }
}

function save_users() {
    fs.writeFileSync("users.json", JSON.stringify(registered_users, null, 2));
}*/

//registered_users = load_users(); move to server.listen //trying to fix render loading error APR 28 EVE

//SERVER
//const wss = new WebSocket.Server({ port: PORT }); no more reliable for the server to work well with Render, REMOVE APR 28 MOR
//console.log("Server is running on port", PORT);
//const http = require("http"); no need anymore, updated to EXPRESS, MAY 2 MOR


//Render port - APR 28 MOR
//const PORT = process.env.Port_Of_Server || 7777; delete APR 28
const PORT = process.env.PORT || 7777;//move to render

/*
const server = http.createServer((req, res) => {
    res.writeHead(200, { "Content-Type": "text/plain" });
    res.end("SecureChat backend running");
});*/ //updated to EXPRESS on MAY 2 MOR

//BackBlaze upload and download
app.post("/upload", async (req, res) => {
  const { fileName, fileBase64 } = req.body;

  const buffer = Buffer.from(fileBase64, "base64");
  const key = `securechat/${Date.now()}_${fileName}`;

  await s3.send(new PutObjectCommand({
    Bucket: process.env.B2_BUCKET,
    Key: key,
    Body: buffer,
    ContentType: "application/octet-stream"
  }));

  res.json({ ok: true, key });
});

app.get("/file/:name", async (req, res) => {
  const key = req.params.name;

  const command = new GetObjectCommand({
    Bucket: process.env.B2_BUCKET,
    Key: key
  });

  const url = await getSignedUrl(s3, command, { expiresIn: 3600 });

  res.json({ url });
});


//debug and submission proof, MAY 2 EVE
app.get("/", (req, res) => {
    res.send("SecureChat backend is RUNNING!!!");
});

app.get("/healthy", (req, res) => {
    res.json({
        status: "ok",
        time: new Date().toISOString()
    });
});

//add to ensure about chat log filder pontentual issue,

if (!fs.existsSync("chat_logs")) {
    fs.mkdirSync("chat_logs");
}

const wss = new WebSocket.Server({ server });

//server.listen(PORT, "0.0.0.0", () => {//forgot to add 0.0.0.0 to actual deploy, add APR 28 EVE
server.listen(PORT, () => { //remove to test RENDER again
    //registered_users = load_users(); removed because nolonger use this function, apr 30 eve
    console.log("Server running on port " + PORT);
    //only use for debug: 
    //console.log("Loaded users:", Object.keys(registered_users)); no longer needed, apr 30 eve
    console.log("MySQL Server is workinggg!!");
});

//HEARTBEAT
setInterval(() => {
    wss.clients.forEach(ws => {
        if (!ws.isAlive) { //prevent dead socket remain online
            removeClient(ws);
            return ws.terminate();
        }
        ws.isAlive = false;
        ws.ping();
    });
}, 12000);

//CONNECTION
wss.on("connection", (ws) => {
    let username = null;

    ws.isAlive = true;

    ws.on("pong", () => {
        ws.isAlive = true;
    });

    //ws.on("message", (raw) => {
    ws.on("message", async (raw) => {
        let data;
        try { data = JSON.parse(raw); }
        catch { return; }

        const type = data.type;

        //AUTH
        /*OLD AUTH UNTIL APR 30 EVE
        if (type === "auth") {
            username = data.username.toLowerCase();
            const pass = data.password;
            
            //for debug purpose
            console.log("login attempt:", username);
           // console.log("user exists:", !! registered_users[username]); APR 30 EVE  No longer use the dict

            if (!registered_users[username] || !check_pass(pass, registered_users[username])) {
                ws.send(JSON.stringify({ type: "auth_fail" }));
                return;
            }

            //clients_connected_dict[ws] = username;
            clients_connected_dict.set(ws, username); //with the new structure, apr30 MOR
            ws.send(JSON.stringify({ type: "auth_success" }));

            // notify everyone
            wss.clients.forEach(c => {
                if (c.readyState === WebSocket.OPEN) {
                    c.send(JSON.stringify({
                        type: "user_joined",
                        username
                    }));
                }
            });

            return;
        }*/

        if (type === "auth") {
            username = data.username.toLowerCase();
            const pass = data.password;

            console.log("Login:", username);

            // rate limiting
            if (!allowed_to_try_login(username)) {
                ws.send(JSON.stringify({
                    type: "auth_fail",
                    message: "Block from login. Too many login attempts!" //a little clear message, updated MAY 4 EVE.
                }));
                return;
            }

            try {
                const [rows] = await db.promise().query(
                    "SELECT password_hash FROM users WHERE username = ?",
                    [username]
                );

                //user not found
                if (rows.length === 0) {
                    record_failed_login(username);//add the feature back
                    ws.send(JSON.stringify({ type: "auth_fail", message: "Login attempt failed (Code:0001A)!"})); 
                    //message is public but reason is private for devs to fix
                    return;
                }

                const hashed = rows[0].password_hash;

                //wrong password
                if (!check_pass(pass, hashed)) {
                    record_failed_login(username); //add the feature back
                    ws.send(JSON.stringify({ type: "auth_fail", message: "Login attempt failed (Code:0010B)!"})); 
                    //message about the fail attempts is public but reason is private for devs to fix. 
                    // //Updated the content of the announcement, MAY 4 EVE
                    return;
                }

                //success login
                clients_connected_dict.set(ws, username);
                delete failed_attempts_dict[username];

                //ws.send(JSON.stringify({ type: "auth_success" }));
                const token = crypto.randomBytes(16).toString("hex");
                session_tokens[username] = token;

                ws.send(JSON.stringify({ type: "auth_success", token }));

                //notify all connected users
                wss.clients.forEach(c => {
                    if (c.readyState === WebSocket.OPEN) {
                        c.send(JSON.stringify({
                            type: "user_joined",
                            username
                        }));
                    }
                });

            } catch (ERROR) {
                console.log("Login error:", ERROR);

                //server error == failed attempt
                record_failed_login(username);

                ws.send(JSON.stringify({ type: "server_error", message: "Login attempt failed (Code:0011C)!"})); 
                //message is public but reason is private for devs to fix //Updated the content of the announcement, MAY 4 EVE
            }

            return;
        }

        // REGISTER, up to apr 30 eve
        /*
        if (type === "register") {
            const username = data.username.toLowerCase();
            const pass = data.password;

            const [valid, msg] = validate_password(pass);
            if (!valid) {
                ws.send(JSON.stringify({ type: "auth_fail", message: msg }));
                return;
            }

            registered_users[username] = hash_pass(pass);
            save_users();

            //add for debug purpose, apr 30
            console.log("registered user:", username);
            console.log("total user:", Object.keys(registered_users));


            ws.send(JSON.stringify({ type: "register_success" }));
            return;
        }*/

        if (type === "register") {
            const username = data.username.toLowerCase();
            const pass = data.password;

            const [valid, msg] = validate_password(pass);
            if (!valid) {
                ws.send(JSON.stringify({ type: "auth_fail", message: msg }));
                return;
            }

            try {
                const [rows] = await db.promise().query(
                    "SELECT id FROM users WHERE username = ?",
                    [username]
                );

                if (rows.length >0) {
                    ws.send(JSON.stringify({ type: "auth_fail", message: "Username exists" }));
                    return;
                }

                const hash = hash_pass(pass);

                await db.promise().query(
                    "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                    [username, hash]
                );

                ws.send(JSON.stringify({ type: "register_success" }));

            } catch (ERROR) {
                console.log("register error:", ERROR);
                ws.send(JSON.stringify({ type: "server_error" }));
            }

            return;
        }

        //get users
        if (type === "get_users") {
            //const list = Object.values(clients_connected_dict);
            const list = Array.from(clients_connected_dict.values());//new structure, apr 30
            ws.send(JSON.stringify({ type: "user_list", users: list }));
            return;
        }

        //now storing the fingerprint and the key MAY 1. MOR
        if (type === "post_public_key") {
            const username = clients_connected_dict.get(ws);
            if (!username) return;

            const PUB_key = data.key;

            // basic validation
            if (typeof PUB_key !== "string" || PUB_key.length < 333) //make sure the key is "String type", NORMALLY the key is at least ~400 character.
                return;

            clients_p_keys[username] = PUB_key;

            const hash_TEXT = crypto
                .createHash("sha256")
                .update(PUB_key)
                .digest("hex");

            public_key_fingerprints[username] = hash_TEXT;

            console.log(`[KEY STORED] ${username} fingerprint: ${hash_TEXT}`);

            return;
        }

        //key request
        if (type === "request_key") {
            const target_user= data.target_user;

            const PUBkey = clients_p_keys[target_user];
            const fingerprint = public_key_fingerprints[target_user];

            if (PUBkey && fingerprint) {
                ws.send(JSON.stringify({
                    type: "key_response", user: target_user, key: PUBkey,fingerprint: fingerprint }));
            }
            return;
        }

        // MESSAGE
        if (type === "message") {
            console.log("mess hit the server!!");
            const token = data.token;

            if (!username || session_tokens[username] !== token) return;

            //if (!allowed_to_send(username)) return; update for clearer messgae on UI
            if (!allowed_to_send(username)) {
                ws.send(JSON.stringify({
                    type: "rate_limit",
                    message: "Too many messages :(. Slow down!!"
                }));
                return;
            }

            const target = data.to;

            console.log("Message flow debugging");
            console.log("from:", username);
            console.log("to:", target);

            wss.clients.forEach(c => {
                const mappedUser = clients_connected_dict.get(c);
                console.log("client:", mappedUser, "| ready:", c.readyState);
            });
    
            wss.clients.forEach(c => {
                if (clients_connected_dict.get(c) === target) {
                    c.send(JSON.stringify({
                        type: "message",
                        from: username,
                        content: data.content,
                        time: getTimeString()
                    }));
                }
            });

            await saveMess(username, target, data.content, "text");

            write_mess_to_log(username, target,
                `${getTimeString()} ${username}: [encrypted]`);
        }

        // FILE, using upto MOR MAY 2, REPLACED BY BACKBLAZE
        /*
        if (type === "file") {
            if (!username || session_tokens[username] !== data.token) return;
            const target = data.to;

            wss.clients.forEach(c => {
                //if (clients_connected_dict[c] === target) {
                if (clients_connected_dict.get(c) === target){
                    c.send(JSON.stringify({
                        type: "file",
                        from: username,
                        filename: data.filename,
                        size: data.size,
                        data: data.data,
                        time: getTimeString()
                    }));
                }
            });

        await saveMess(username, target, null, "file", data.filename, data.size);      
        }*/

        if (type === "file") {
            if (!username || session_tokens[username] !== data.token) return;
            const target = data.to;

            try {
                const buffer = Buffer.from(data.data, "base64");
                const fileUrl = await BBupload(data.filename,  buffer, data.filetype || "application/octet-stream" );

                // send to receiver
                wss.clients.forEach(c => {
                    if (clients_connected_dict.get(c) === target) {
                        c.send(JSON.stringify({type: "file",  from: username, filename: data.filename, url: fileUrl,  time: getTimeString()  }));
                    }
                });

                await saveMess(username, target, fileUrl, "file", data.filename);

            } catch (err) {
                console.log("Error in uploading process:", err);
            }
        }


        // TYPING
        if (type === "typing") {
            const target = data.to;

            wss.clients.forEach(c => {
                //if (clients_connected_dict[c] === target) {
                if (clients_connected_dict.get(c) === target){
                    c.send(JSON.stringify({
                        type: "typing",
                        from: username
                    }));
                }
            });
        }

        //if (type === "ping") {
        //    ws.send(JSON.stringify({ type: "pong" }));
        //}

        if (type === "get_history") {
            const firstUser = username;
            const secondUser = data.with;

            try {
                const [rows] = await db.promise().query(
                    `SELECT * FROM messages 
                    WHERE (sender=? AND receiver=?) 
                    OR (sender=? AND receiver=?) 
                    ORDER BY created_at ASC`,
                    [firstUser, secondUser, secondUser, firstUser]
                );

                ws.send(JSON.stringify({
                    type: "history",
                    with: secondUser,
                    messages: rows
                }));

            } catch (err) {
                console.log("history error:", err);
            }
        }
    });

    //ws.on("error", () => removeClient(ws));
    //ws.on("close", () => removeClient(ws));
   
    //debug code MAY 4 EVE for the popup "Sever closed connection"
    ws.on("close", () => {
        console.log("close event", username, new Date().toISOString());
        removeClient(ws);//test finnished, recovered this feature.
    });

    ws.on("error", (err) => {
        console.log("error event", err, username);
        removeClient(ws);//test finnished, recovered this feature.
    });

});

