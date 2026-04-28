// SecureChat Node Ver
// APR 26: Porting from Python. Python time is not supported, so new time functions created.

const WebSocket = require("ws");
const fs = require("fs");
const path = require("path");
const bcrypt = require("bcrypt");
const crypto = require("crypto");
const glob = require("glob"); // MAR 15 EVE: To fix the numbering session error after TURN OFF Server

//Render port - APR 28 MOR
//const PORT = process.env.Port_Of_Server || 7777; delete APR 28
const PORT = process.env.PORT || 7777; //move to render

let registered_users = {};
let clients_connected_dict = {}; // store name of client
let clients_p_keys = {};
let last_pong = {}; // tracking last pong message
let active_chat_pairs = new Set();
let chat_sessions = {}; // MAR 10 eve: needed for the new chatfile system
let aes_session_keys = {};
let heartbeat_failures = {};
let failed_attempts_dict = {}; // MAR 7: Block login
let user_timestamp_dict = {}; // rate limit

const mess_limit = 5;
const time_range = 8;

const max_attempts_allowed = 3;
const block_login_time = 10;



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

//USER STORAGE
function load_users() {
    try {
        return JSON.parse(fs.readFileSync("users.json", "utf8"));
    } catch {
        return {};
    }
}

function save_users() {
    fs.writeFileSync("users.json", JSON.stringify(registered_users, null, 2));
}

registered_users = load_users();

//SERVER
//const wss = new WebSocket.Server({ port: PORT }); no more reliable for the server to work well with Render, REMOVE APR 28 MOR
//console.log("Server is running on port", PORT);
const http = require("http");

const server = http.createServer();
const wss = new WebSocket.Server({ server });

server.listen(PORT, () => {
    console.log("Server running on port " + PORT);
});


//HEARTBEAT
setInterval(() => {
    Object.keys(clients_connected_dict).forEach(ws => {
        try {
            ws.send(JSON.stringify({ type: "ping" }));
        } catch {}
    });
}, 12000);

//CONNECTION
wss.on("connection", (ws) => {
    let username = null;

    ws.on("message", (raw) => {
        let data;
        try { data = JSON.parse(raw); }
        catch { return; }

        const type = data.type;

        // AUTH
        if (type === "auth") {
            username = data.username.toLowerCase();
            const pass = data.password;

            if (!registered_users[username] || !check_pass(pass, registered_users[username])) {
                ws.send(JSON.stringify({ type: "auth_fail" }));
                return;
            }

            clients_connected_dict[ws] = username;
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
        }

        // REGISTER
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

            ws.send(JSON.stringify({ type: "register_success" }));
            return;
        }

        // GET USERS
        if (type === "get_users") {
            const list = Object.values(clients_connected_dict);
            ws.send(JSON.stringify({ type: "user_list", users: list }));
            return;
        }

        // PUBLIC KEY STORE
        if (type === "post_public_key") {
            clients_p_keys[username] = data.key;
            return;
        }

        // KEY REQUEST
        if (type === "request_key") {
            const target = data.target_user;
            const key = clients_p_keys[target];

            if (key) {
                ws.send(JSON.stringify({
                    type: "key_response",
                    user: target,
                    key: key
                }));
            }
            return;
        }

        // MESSAGE
        if (type === "message") {
            if (!allowed_to_send(username)) return;

            const target = data.to;

            wss.clients.forEach(c => {
                if (clients_connected_dict[c] === target) {
                    c.send(JSON.stringify({
                        type: "message",
                        from: username,
                        content: data.content,
                        time: getTimeString()
                    }));
                }
            });

            write_mess_to_log(username, target,
                `${getTimeString()} ${username}: [encrypted]`);
        }

        // FILE
        if (type === "file") {
            const target = data.to;

            wss.clients.forEach(c => {
                if (clients_connected_dict[c] === target) {
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
        }

        // TYPING
        if (type === "typing") {
            const target = data.to;

            wss.clients.forEach(c => {
                if (clients_connected_dict[c] === target) {
                    c.send(JSON.stringify({
                        type: "typing",
                        from: username
                    }));
                }
            });
        }

        if (type === "ping") {
            ws.send(JSON.stringify({ type: "pong" }));
        }
    });

    ws.on("close", () => {
        const user = clients_connected_dict[ws];
        delete clients_connected_dict[ws];

        wss.clients.forEach(c => {
            if (c.readyState === WebSocket.OPEN) {
                c.send(JSON.stringify({
                    type: "user_left",
                    username: user
                }));
            }
        });
    });
});