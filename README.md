# SecureChat

Project for CPSC 455 (Web Security) Spring 2026 - Group 3 - Cal State Fullerton

SecureChat is a real-time chat app we built for our semester project. The goal was to make a secure messaging system that works over the internet without using something like Slack or Teams. We built it in 3 phases throughout the semester, starting from a basic terminal chat and ending with a cloud-hosted web app.

---

## Group Members

- Yaser Mohtaseb Zada
- Tien Dat Le
- Karla Ramirez

---

## Phases

### Phase 1 - Terminal Chat (Basic Prototype)
First version of SecureChat. Everything runs in the terminal, nothing fancy.

**What we added:**
- User registration and login (passwords hashed with bcrypt)
- Real-time messaging between users
- TLS using a self-signed certificate
- Rate limiting (5 messages per 8 seconds)
- Heartbeat system so the server knows if a client disconnects, auto-reconnects after 2 seconds
- Basic file transfer with /file command

**Known issues / limitations:**
- No GUI, terminal only
- Self-signed cert so browsers will throw a warning
- No chat history saved
- Password validation is pretty basic

---

### Phase 2 - GUI + Encryption + LAN
We rebuilt the client as a browser app and added a lot of security stuff.

**What we added:**
- Browser-based GUI (HTML/CSS/JS)
- End-to-end encryption (AES-256-GCM for messages, RSA-4096 for key exchange)
- Brute force protection on login
- File transfers now encrypted too
- Emoji support
- Users can switch between chats without closing the app
- Chat logs saved as .txt files per session
- All authentication happens server-side now

---

### Phase 3 - Cloud Hosted / Internet Accessible (Current)
Moved everything to the cloud so it works over the internet, not just on LAN.

**What we added:**
- Frontend hosted online, accessible from any browser
- WebSocket server deployed on Render (InfinityFree doesn't support WebSockets)
- MySQL database for storing users and encrypted messages
- Cloud file storage for file transfers
- Online/offline/typing indicators
- Auto-reconnect if connection drops
- UptimeRobot to keep the server alive
- HTTPS and WSS enforced

**Note: The app will stay live until May 25th 2026 for grading.**

---

## Tech Stack

- Frontend: HTML, CSS, JavaScript
- Backend: Python (websockets)
- Database: MySQL
- File Storage: Firebase / Backblaze B2
- Encryption: AES-256-GCM + RSA-4096
- Password Hashing: bcrypt
- WebSocket Hosting: Render
- Frontend Hosting: InfinityFree
- Uptime: UptimeRobot

---

## How to Run (Local)

```bash
git clone https://github.com/EricTienLe/SecureChat.git
cd SecureChat
pip install -r requirements.txt
```

1. Run `python server.py`
2. Open the browser client
3. Register or log in
4. Start chatting, use `/file yourfile.txt` to send a file

---

## File Structure
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
- Approximate release date: May 7th, 2026.


