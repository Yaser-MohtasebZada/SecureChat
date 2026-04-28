const WebSocket = require("ws");

// create connection FIRST
const ws = new WebSocket("ws://localhost:7777");

ws.on("open", () => {
    console.log("Connected to SecureChat server");

    // STEP 1: register (safe test flow)
    ws.send(JSON.stringify({
        type: "register",
        username: "testuser",
        password: "Test1234"
    }));

    // STEP 2: login after short delay
    setTimeout(() => {
        ws.send(JSON.stringify({
            type: "auth",
            username: "testuser",
            password: "Test1234"
        }));
    }, 1000);

    // STEP 3: send message after login attempt
    setTimeout(() => {
        ws.send(JSON.stringify({
            type: "message",
            to: "anotheruser",
            content: "Hello from test client!"
        }));
    }, 2000);
});

ws.on("message", (data) => {
    console.log("Server says:", data.toString());
});

ws.on("close", () => {
    console.log("Disconnected");
});

ws.on("error", (err) => {
    console.log("Error:", err.message);
});