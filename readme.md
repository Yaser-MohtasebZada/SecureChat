# SecureChat
- Project 1 of CPSC 455 Class, Spring 2026. Group 3
- SecureChat is a basic chat that works on a GUI that allows users to register and chat in real-time, sending files, URLs, and emojis while also ensuring that their credentials are safely protected by the chat system. In this first phase of the semester project, Group 3 members decided to fulfill the requirements that are listed and postpone the in-depth development of features for future updates. As a response to phase 2's requirements, members of Group 3 developed a GUI to replace the terminal system and an HTML file for loading clients. Some main features are conducted, which include, but are not limited to E2EE, emojis, URL sending, multiple chat rooms, and chatlog management.

# Features
## PHASE 1
- Feature 1: User authorization: Users can create accounts and log in to chat in this system. The goal is to make sure that each user is identified in the chat history, where multiple users can join the same chat. Passwords are hashed using bcrypt library.
Feature 2: Real-time chat: Users can chat with each other in real time, ensuring that chatting through the Internet feels similar to talking in person. Join and leave announcements are also broadcast by the server.
- Feature 3: Secure Connection: Using the concept of TLS to protect the message that is transmitted through the server. 
- Feature 4: Rate limiting. Only allow users to send 5 messages in 8 seconds. Prevent spamming the system.
- Feature 5: Heartbeat controlling. Server send 'Ping' and waits for the client to send 'Pong' signal back. Client disconnected is announced to the chat. The client will try to automatically reconnect to the server after 2 seconds of disconnection.
- Feature 6: File transfer. Basic file transfer that allows users send files to other users of the chat.

## PHASE 2
In addition to the Phase 1 features:
- Feature 1: GUI, user-friendly approach for the chat app. Allowed multiple chat conversations by switching chat tabs.
- Feature 2: Emoji options (including emoji picker), sending URL (2 different methods), file and text formatting. We also have a different format for codes that are shared in the chat messages.
- Feature 3: End-to-end encryption. The server no longer accesses the real content of the message between users.
- Feature 4: Brute-force prevention. Server is ready to close connections, then make the malicious user wait 10 seconds after this "users" exceeds the allowed login attempts.  The server no longer accesses the real content of the message between users.
- Feature 5: Chat logs session management. Sessions are numbered by pair, not the person who starts the conversations.
- Feature 6: Real server hosting where clients can connect from different networks and devices.

# Installation
## Clone the repo
git clone <https://github.com/EricTienLe/SecureChat.git>
cd SecureChat

## Install Dependencies
pip install -r requirements.txt

## Step-by-step to running the server
1. In your downloaded folder, python server.py
2. Also in the same downloaded folder, run securechat_client.html file to loading the GUI.
3. Type in desired username (if you have not registered yet, the system will use this username), register/login
4. Start the chat, including send files, url and emojis.

# Limitations
- The password and username validation are basic.
- Self-signed certificate.
- Does not have chat history.

# Future developments
- In-depth user creation and validation.
- Storing user chat history in each group chat.
- Allow group chat.
- Allow sending pictures and GIFs.

# A running demo 
- The link will be posted after the demo is made:
- 

- The link will be posted after the demo for Phase 2 is made:
- Approximate release date: March 21, 2026.

# Authors
Group 3 of CPSC 455 Spring 2026


