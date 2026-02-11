# SecureChat
- Project 1 of CPSC 455 Class, Spring 2026. Group 3
- SecureChat is a very basic chat that works on terminals that allow users to register and chat in real-time, sending files while also ensuring that their credentials are safely protected by the chat system. In this first phase of the semester project, Group 3 members decided to fulfill the requirements that are listed and postpone the in-depth developments of features for the furture updates.

# Features
- Feature 1: User authorization: Users can create accounts and log in to chat in this system. The goal is to make sure that each user is identified in the chat history, where multiple users can join the same chat. Passwords are hashed using bcrypt library.
Feature 2: Real-time chat: Users can chat with each other in real time, ensuring that chatting through the Internet feels similar to talking in person. Join and leave announcements are also broadcast by the server.
- Feature 3: Secure Connection: Using the concept of TLS to protect the message that is transmitted through the server. 
- Feature 4: Rate limiting. Only allow users to send 5 messages in 8 seconds. Prevent spamming the system.
- Feature 5: Heartbeat controlling. Server send 'Ping' and waits for the client to send 'Pong' signal back. Client disconnected is announced to the chat. The client will try to automatically reconnect to the server after 2 seconds of disconnection.
- Feature 6: File transfer. Basic file transfer that allows users send files to other users of the chat.

# Installation
## Clone the repo
git clone <https://github.com/EricTienLe/SecureChat.git>
cd SecureChat

## Install Dependencies
pip install -r requirements.txt

## Step-by-step to running the server
1. In your downloaded folder, python server.py
2. Also in the same downloaded folder, run python firstClient.py for the 1st Client and python secondClient.py for the 2nd Client
3. Type in desired username (if you have not registered yet, the system will use this username), register/login
4. Start the chat or send files (Starting with /file 'yourfile.txt').

# Main files in folders of the project
SecureChat
├── server.py  #server file
├── firstClient.py  #client file
├── secondClient.py  #client file
├── certificate
│   ├── certificate.pem  #not uploaded to GitHub reasons
│   └── privateKey.pem #not uploaded to GitHub reasons
└── users.json #not uploaded to GitHub for security reasons

# Limitations
- The password and username validation are basic.
- There is no GUI for the project.
- Self-signed certificate to mimic TLS.
- Does not have chat history.

# Future developments
- In-deptH user creation and validation.
- In details handling the system and client connection.
- Storing user chat history.
- A basic GUI for the SecureChat.

# A running demo 
- The link will be posted after the demo be made:
- Approximate release date: February 13, 2026.

# Authors
Group 3 of CPSC 455 Spring 2026

