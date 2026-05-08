// SecureChat Node Ver
// APR 26: Porting from Python. Python time is not supported, so new time functions created.
// Tien Dat Le, Yaser Mohtaseb Zada, Karla Ramirez

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
const crypto = require("crypto"); //recover  
const crypto_subtle = require("crypto").webcrypto.subtle;

const glob = require("glob"); // MAR 15 EVE: To fix the numbering session error after TURN OFF Server
const mysql = require("mysql2"); //APR 30 EVE: To test Database on Infinity free, using mysql2 library

//EXPRES update, MAY 2 MOR
const express = require("express");
const app = express();
app.use(express.json({ limit: "23mb" }));
app.use(express.static(path.join(__dirname, '../htmlRender'))); //CACHE ISSUES MAKE INFINITY FREE IMPOSSIBLE TO TEST, MAY 6 EVE


const server = require("http").createServer(app)

if (!process.env.MYSQL_PUBLIC_URL) {
    throw new Error("MYSQL_PUBLIC_URL is missing in environment variables");
}

const dbUrl = new URL(process.env.MYSQL_PUBLIC_URL); 
const db = mysql.createPool({ host: dbUrl.hostname, user: dbUrl.username, password: dbUrl.password, database: dbUrl.pathname.replace(/^\/+/, ""), port: dbUrl.port || 3306 });
console.log("DB URL loaded:", !!process.env.MYSQL_PUBLIC_URL);

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

//Using BackBlaze [BB]; update private bucket
async function BBupload(filename, buffer, mimetype) {
    const key = `securechat/${Date.now()}_${filename}`;

    await s3.send(new PutObjectCommand({
        Bucket: process.env.B2_BUCKET,
        Key: key,
        Body: buffer,
        ContentType: mimetype
    }));

    // generate signed URL for private bucket (valid 1 hour)
    const signedUrl = await getSignedUrl(s3, new GetObjectCommand({
        Bucket: process.env.B2_BUCKET,
        Key: key
    }), { expiresIn: 3600 });

    return signedUrl;
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

    if (user && ws.token && session_tokens[user]) {
    session_tokens[user].delete(ws.token);
}
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

//Render port - APR 28 MOR
//const PORT = process.env.Port_Of_Server || 7777; delete APR 28
const PORT = process.env.PORT || 7777;//move to render

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


app.get("/healthy", (req, res) => {
    res.json({
        status: "ok",
        time: new Date().toISOString()
    });
});

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
        //console.log("server recieved raw:", raw.toString()); DEBUG ENDED MAY 7, EVE
        let data;
        try { data = JSON.parse(raw); }
        catch { return; }

        const type = data.type;

        if (type === "auth") {
            username = data.username.toLowerCase();
            const pass = data.password;

            //console.log("Login:", username); debug ended may 7, eve

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

                const token = crypto.randomBytes(16).toString("hex");

                //initialize set if not exist
                if (!session_tokens[username]) {
                    session_tokens[username] = new Set();
                }

                //store token
                session_tokens[username].add(token);

                //attach to socket 
                ws.token = token;
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

            //forget to add to DB

            await db.promise().query(
                `UPDATE users SET public_key = ? WHERE username = ?`,
                [PUB_key, username]
            );

            console.log(`[KEY STORED] ${username} fingerprint: ${hash_TEXT}`);

            return;
        }

        if (type === "request_key") {
            const target_user = data.target_user;
            const requester = clients_connected_dict.get(ws);

            const requesterPubKey = clients_p_keys[requester];

            //if target's public key IS NOT in memory (offline), load from DB
            if (!clients_p_keys[target_user]) {
                try {
                    const [pkRows] = await db.promise().query(
                        `SELECT public_key FROM users WHERE username = ?`,
                        [target_user]
                    );
                    if (pkRows.length > 0 && pkRows[0].public_key) {
                        clients_p_keys[target_user] = pkRows[0].public_key;
                        const fp = crypto.createHash("sha256").update(pkRows[0].public_key).digest("hex");
                        public_key_fingerprints[target_user] = fp;
                    }
                } catch(e) {
                    console.log("Failed to load public key from DB:", e);
                }
            }

            if (!requesterPubKey || !clients_p_keys[target_user]) return;
            const fingerprint = public_key_fingerprints[target_user];
            if (!fingerprint) return;

            try {
                const pemBody = requesterPubKey
                    .replace(/-----BEGIN PUBLIC KEY-----/, '')
                    .replace(/-----END PUBLIC KEY-----/, '')
                    .replace(/\s+/g, '');
                const keyBuffer = Buffer.from(pemBody, 'base64');

                const importedKey = await crypto_subtle.importKey(
                    "spki", keyBuffer,
                    { name: "RSA-OAEP", hash: "SHA-256" },
                    false, ["encrypt"]
                );

                const aesKey = await crypto_subtle.generateKey(
                    { name: "AES-GCM", length: 256 }, true, ["encrypt", "decrypt"]
                );

                const rawAES = await crypto_subtle.exportKey("raw", aesKey);

                const encryptedAES = await crypto_subtle.encrypt(
                    { name: "RSA-OAEP" }, importedKey, rawAES
                );

                const encryptedB64 = Buffer.from(new Uint8Array(encryptedAES)).toString('base64');

                // send to requester
                ws.send(JSON.stringify({
                    type: "key_response",
                    user: target_user,
                    key: encryptedB64,
                    fingerprint: fingerprint
                }));

                // send same AES key to target user, encrypted with their public key
                const targetPubKey = clients_p_keys[target_user];
                if (targetPubKey) {
                    const targetPemBody = targetPubKey
                        .replace(/-----BEGIN PUBLIC KEY-----/, '')
                        .replace(/-----END PUBLIC KEY-----/, '')
                        .replace(/\s+/g, '');
                    const targetKeyBuffer = Buffer.from(targetPemBody, 'base64');

                    const targetImportedKey = await crypto_subtle.importKey(
                        "spki", targetKeyBuffer,
                        { name: "RSA-OAEP", hash: "SHA-256" },
                        false, ["encrypt"]
                    );

                    const encryptedAESforTarget = await crypto_subtle.encrypt(
                        { name: "RSA-OAEP" }, targetImportedKey, rawAES
                    );

                    const encryptedB64forTarget = Buffer.from(new Uint8Array(encryptedAESforTarget)).toString('base64');

                    //send to target user
                    wss.clients.forEach(c => {
                        if (clients_connected_dict.get(c) === target_user) {
                            c.send(JSON.stringify({
                                type: "key_response",
                                user: requester,
                                key: encryptedB64forTarget,
                                fingerprint: public_key_fingerprints[requester]
                            }));
                        }
                    });

                    // save both encrypted keys to DB
                    try {
                        const pair = [requester, target_user].sort();
                        await db.promise().query(
                            `INSERT INTO session_keys (user1, user2, encrypted_key_for_user1, encrypted_key_for_user2)
                            VALUES (?, ?, ?, ?)`,
                            [
                                pair[0], pair[1],
                                pair[0] === requester ? encryptedB64 : encryptedB64forTarget,
                                pair[0] === requester ? encryptedB64forTarget : encryptedB64
                            ]
                        );
                        console.log(`[SESSION KEY SAVED] for pair: ${pair[0]} / ${pair[1]}`);
                    } catch (err) {
                        console.log("Session key save error:", err);
                    }
                }

            } catch (err) {
                console.log("Key exchange error:", err);
            }

            return;
        }

        // MESSAGE
        if (type === "message") {
            console.log("mess hit the server!!");
            const token = data.token;
            const target = data.to;
            
            if (!username) {
                console.log("No username bound to this socket");
                return;
            }
            
            if (!session_tokens[username]?.has(token)) {
                console.log("DROP: invalid token");
                return;
            }

            //rate limting
            if (!allowed_to_send(username)) {
                ws.send(JSON.stringify({
                    type: "rate_limit",
                    message: "Too many messages :(. Slow down!!"
                }));
                return;
            }

            wss.clients.forEach(c => {
                if (clients_connected_dict.get(c) === target) {
                    c.send(JSON.stringify({
                        type: "message",
                        from: username,
                        content: data.content,
                        token: token, //found the issues, missing this all the time, NOON MAY 5
                       // time: getTimeString() fix time mismatch, MAY 6 EVE let client generate the time
                    }));
                }
            });

            await saveMess(username, target, data.content, "text");

            write_mess_to_log(username, target,
                `${getTimeString()} ${username}: [encrypted]`);
        }

        if (type === "file") {
            //if (!username || session_tokens[username] !== data.token) return;
            if (!username || !session_tokens[username]?.has(data.token)) {
                console.log("file is dropped: invalid token");
                return;
            }
            const target = data.to;

            try {
                const buffer = Buffer.from(data.data, "base64");
                const fileUrl = await BBupload(data.filename,  buffer, data.filetype || "application/octet-stream" );

                // send to receiver
                wss.clients.forEach(c => {
                    wss.clients.forEach(c => {
                        const u = clients_connected_dict.get(c);
                        if (u === target || u === username) {
                            c.send(JSON.stringify({type: "file", from: username, filename: data.filename, url: fileUrl, time: getTimeString()}));
                        }
                    });
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

        if (type === "get_history") {
            const firstUser = username;
            const secondUser = data.with;

            try {
                // fetch messages first
                const [rows] = await db.promise().query(
                    `SELECT * FROM messages 
                    WHERE (sender=? AND receiver=?) 
                    OR (sender=? AND receiver=?) 
                    ORDER BY created_at ASC`,
                    [firstUser, secondUser, secondUser, firstUser]
                );

                const pair = [firstUser, secondUser].sort();
                const [keyRows] = await db.promise().query(
                    `SELECT * FROM session_keys 
                    WHERE user1=? AND user2=?
                    ORDER BY created_at ASC`,
                    [pair[0], pair[1]]
                );

                //return ALL saved keys for this pair
                const allKeysForMe = keyRows.map(row =>
                    pair[0] === firstUser
                        ? row.encrypted_key_for_user1
                        : row.encrypted_key_for_user2
                );

                ws.send(JSON.stringify({
                    type: "history",
                    with: secondUser,
                    messages: rows,
                    session_keys: allKeysForMe
                }));

            } catch (err) {
                console.log("history error:", err);
            }
        }
    });
   
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

