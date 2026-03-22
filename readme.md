# SecureChat
* Project 1 of CPSC 455 Class, Spring 2026. Group 3
* SecureChat is a basic chat that works on a GUI that allows users to register and chat in real-time, sending files, URLs, and emojis while also ensuring that their credentials are safely protected by the chat system. In this first phase of the semester project, Group 3 members decided to fulfill the requirements that are listed and postpone the in-depth development of features for future updates. As a response to Phase 2's requirements, members of Group 3 developed a GUI to replace the terminal system and an HTML file for loading clients. Some main features include, but are not limited to, E2EE, emojis, URL sending, multiple chat rooms, and chat log management.

## ⚠️ Important — Browser Requirement
**You must use Firefox.** Chrome and Edge block self-signed certificates and will refuse the WSS connection. Download Firefox at https://www.mozilla.org/firefox before running the client.

## Features

### PHASE 1
* Feature 1: User authorization: Users can create accounts and log in to chat in this system. The goal is to make sure that each user is identified in the chat history, where multiple users can join the same chat. Passwords are hashed using bcrypt library.
* Feature 2: Real-time chat: Users can chat with each other in real time, ensuring that chatting through the Internet feels similar to talking in person. Join and leave announcements are also broadcast by the server.
* Feature 3: Secure Connection: Using the concept of TLS to protect the message that is transmitted through the server.
* Feature 4: Rate limiting. Only allow users to send 5 messages in 8 seconds. Prevent spamming the system.
* Feature 5: Heartbeat controlling. Server send 'Ping' and waits for the client to send 'Pong' signal back. Client disconnected is announced to the chat. The client will try to automatically reconnect to the server after 2 seconds of disconnection.
* Feature 6: File transfer. Basic file transfer that allows users to send files to other users of the chat.

### PHASE 2
In addition to the Phase 1 features:
* Feature 1: GUI, user-friendly approach for the chat app. Allows multiple chat conversations by switching chat tabs.
* Feature 2: Emoji options (including emoji picker), sending URLs (2 different methods), file and text formatting. A different format for code snippets shared in chat messages.
* Feature 3: End-to-end encryption. The server no longer accesses the real content of the message between users.
* Feature 4: Brute-force prevention. Server closes the connection and makes the user wait 10 seconds after exceeding the allowed login attempts.
* Feature 5: Chat log session management. Sessions are numbered by pair, not by the person who starts the conversation.
* Feature 6: Real server hosting where clients can connect from different networks and devices.

## Installation

### Clone the repo
```
git clone https://github.com/EricTienLe/SecureChat.git
cd SecureChat
```

### Install Dependencies
```
pip install -r requirements.txt
```

## Step-by-step to running the server
1. In your downloaded folder, run `python server/server.py`
2. Open `securechat_client.html` in **Firefox** to load the GUI
3. If you are a new user, go to the **Register** tab and type a desired username and password. If you already have an account, use the **Login** tab.
4. Start the chat, including sending files, URLs, and emojis.

## Main files in folders of the project
```
SecureChat
├── server/
│   └── server.py              # server file
├── client/
│   ├── firstClient.py         # Python client with E2EE
│   └── secondClient.py        # Python client
├── securechat_client.html     # browser GUI client (open in Firefox)
├── certificate/
│   ├── certificate.pem        # not uploaded to GitHub
│   └── privateKey.pem         # not uploaded to GitHub
├── chat_logs/                 # auto-generated chat logs folder
├── .env                       # not uploaded to GitHub
├── .env.example               # template for .env setup
├── requirements.txt
├── changelog.md
└── users.json                 # not uploaded to GitHub for security reasons
```

## Limitations
* The password and username validation are basic.
* Self-signed certificate (must use Firefox — Chrome and Edge not supported).
* Does not have persistent chat history after server restart.
* File size is limited to 3 KB for the Python clients.

## Future developments
* In-depth user creation and validation.
* In-depth handling of the system and client connection.
* Storing user chat history persistently.
* Allow group chat.
* Allow sending pictures and GIFs.

## A running demo
* https://drive.google.com/drive/folders/1OhmCwARyRZMysAjjciRvEjoFIAJ9Gh0b?usp=drive_link

## Authors
Group 3 of CPSC 455 Spring 2026