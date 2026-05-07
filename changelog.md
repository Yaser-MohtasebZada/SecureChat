Summary of changes of the Project 1
CPSC 455 - GROUP 3 - SPRING 2026
---


# 2 FEB 2026
## Added
- Created project repo on GitHub
- Add collaborators to the project
- Created project skeleton:
 + server (server.py)
 + client (firstClient.py, secondClient.py)
 + certificate (privateKey.pem, certificate.pem)
 - Pushed those files to GitHub.

## Planned
- Write functions to get and send a message
- Test transfer messages

# 3 FEB 2026 (Released to v0.1)
## Added
- Testing async, testng tls
- Write a function to serve clients
- Remove keys from GitHub
- Sending one message to test sending
- Create changelog.md

## Planned
- Develop the sending message to be able to send more messages
- Set the date to write readme.md

# 4 FEB 2026 (Released to v0.2)
## Added
- TLS for server.py and firstClient.py
- Change "ws" to "wss".

# 6 FEB 2026
## Added
- Using a set to identify connected and disconnected users
- Trying to handling discruption
- Write basic get message and send message functions
- Trying to make system_announcement work

## Planned
- Handling messages in real-time
- Handling the disruption
- Label the name of the clients sending the message
- Make the system announcement work
- Testing using sa plit terminal

# 7 FEB 2026 (Released to v0.3)
## Added
- Successfully create real-time chat by testing using split terminal
- Label basically the username of the users
- System announcements now work when a user leaves or joins

## Planned
- Have to create authentication and password + username for each user.

# 8 FEB 2026
## Added
- Basic check and validate username and password

## Planned
- Have to create rate limiting.

# 8 FEB 2026 (Released to v0.4)
## Added
- Create basic rate limiting
- Fix bugs and terminal presentation.

## Planned
- Have to create heartbeat function.
- Look up the file transfer functions.
- Fix bugs and loops when users chat

# 9 FEB 2026 (Released to v0.5)
## Added
- Basic heartbeat and file transfer.

## Planned
- Documentations, fix bugs, and maybe develop some easy-to-do functions.
- Plan for recording.

# 10 FEB 2026 (Released to v0.5.1)
## Added
- File transfer from client to server now become client to client
- Fix some bugs related to the text message
- Update the system receive message announcement

## Planned
- Documentation, especially focus on readme.md

- # 11-12 FEB 2026 (Documentation)
## Done
- Documentation, especially focus on readme.md
- Try to fix the label bug.
- Testing git clone on other machine (SAN is a new priority for the next phase).
- Recording videos for the project.
- Update, fixing bugs and typos in readme.md.

# 13 FEB 2026
## Done
- Fixing typos and final updates on Changelog.md
- Clone the file to the team leader to submit
- All members checked the content of the submission and the requirements
- Upload the required files to Canvas.

# 6 MAR 2026 (Released to v0.6)
## Added
- Fix file conflicts
- Add SAN system, import the hidden real IP of the server
- Update the path of the file system
- Solved the conflict between README.MD and readme.md

## Planned
- Look forthe  next requirement steps
- Double-check and assign the GUI development process

# 7 MAR 2026 (Released to v0.7)
## Added
- Officially update the changelog.md
- Basic brute-force
- First steps of emojis

## Planned
- Develop more of the emoji systems
- Create emojis selection chart
- Update the last phase file transfer process to allow bigger files.

# 8 MAR 2026
## Added
- Emoji chart
- E2E Encryption

## Planned
- Chat Log
- Update the last phase file transfer process to allow bigger files.

## Note:
- Can not upload to Git due to a crash

# 9 MAR 2026
## Added
- GUI in process
- Chat Log
- FIXED E2E Encryption incorrect implements, fixed bugs that crashed the system

## Planned
- Fix the label issues
- Text formatting when the GUI is finished

## Note:
- Can not upload to Git due to a crash with two major issues.

# 10 MAR 2026 Afternoon (Released to v0.8)
## Added
- GUI in process
- Fixed label loop
- Fixed hidden messages between users
- Fixed the crash caused by 

## Planned
- Connect with the GUI
- Link text format and Emojis on the GUI
- Fix chatlog to ensure separate storage
- Look at potentially updating file transfer.

# 10 MAR 2026 Evening 
## Added
- Tried to fix "your message: " issue
- Implement basic file secure transfer
- Fixed chatlog storage file name with session number

## Planned
- Connect with the GUI
- Link text format and Emojis on the GUI
- Video recording plans

# 11 MAR 2026 
## Added
- Trying to connect the GUI with the backend code

## Planned
- Connect with the GUI
- Link text format and Emojis on the GUI
- Testing the connection between clients and the server on the network

# 12 MAR 2026 
## Added
- GUI finished
- Fixed firewall rules to allow access from other machines to sthe erver.
- Changed the server.py to adapt to the GUI
- Fix features that are in trouble for switching from terminal-based to GUI-based

## Planned
- The HTML works well with the GUI

## Progress
- The server actually connected and passed the authentication of the GUI, after testing with WS and WSS.
- Decided client.py is no longer needed for the project.

# 13 MAR 2026 
## Added
- Continuing to fix bugs in both server.py and client.html
- Update the file forward with the encryption
- Fixing bugs and ensuring the encryption functions work

## Planned
- The HTML works well with the GUI, giving actual access to the chat

# 13 MAR 2026 EVE (Released to v0.9)
## Added
- A Certificate file for Chrome (test unsuccessfully)

## Progress
- The first time you can access the chat room

## Planned
- Fix the chat bugs. Currently, only send the encrypted message through the chat
- Users easily go offline, so it needs to be focused
- Testing with the 3rd account

# 14 MAR 2026 (Released to v0.9.1)
## Fixed
- Now two users can see the plaintext message

## Progress
- Dealing with very strict Chrome requirements with SAN, may have to test on different devices USING Firefox.

## Planned
- Users easily go offline, so it needs to be focused
- Testing with the 3rd account

# 14 MAR 2026 EVE 
- First time there is a client connection from the 2nd device

## Planned
- Users easily go offline, fixing

# 15 MAR 2026 (Released to v0.9.2)
## Tested
- Three users text separately in pairs
- Tested three users successfully
- Fixed the chat textfield moving and hiding issues
- Fix the session numbering system of the chat log
- Rechecked the file sending and rechecked the emoji pickers, sending emojis.

## Progress
- Using Firefox multi-account to test, because Chrome and Edge do not support self-signed certificates

## Planned
- Formally edit this changelog writing styles
- Formally add and rewrite the user guide
- Test text formatting issues
- Documentary
- Plan to video record.

# 15 MAR 2026 EVE (Released to v0.9.3)
## Add
- Fixed new session numbering issues (track number after server is disconnected)
- Clickable link in the chat
- Remove and add some emojis.

## Progress
- Tested text formatting issues
- Download the needed Firefox on the 2nd device to test clients on a different device with the server. 
- Tested 3 clients on different devices from the server as required.

## Planned
- Double-check for minor bugs and issues before release v1.0
- Formally edit this changelog writing styles, add, and rewrite the user guide
- Documentary, plan to video record.

# 17 MAR 2026
## Progress
- Tested on campus and made sure the server is working, noted that clients are on different machines with the server.

# 19 MAR 2026 (Released to v1.0)
## Add
- Notes for presentation.
- Updated new user guide (readme). Noted that members of the group decided to remove the file structure of the project to avoid fingerprinting attacks.
- Updated the changelog

## Progress
- Tested the 2nd time to make sure all features worked.

# 25-26 APR 
## Progress
- Conver old style Python server to the new Node server
- Testing.

# 27 APR 2026 EVE
- Branched to Phase 3 branch
- Testing some cloud preparation for switching up.
- Download Node LTS on the server machine.

## Planned
- Convert HTML file
- Upload first updated version.

# 28 APR 2026 MOR
## Progress
- Fix many bugs on new server.js
- Download glob
- Push main code to Github

## Planned
- Render employement

# 28 APR 2026 EVE
## Progress
- Render registration
- Got the URL: https://securechat-fp59.onrender.com/
- Fix bugs when upload to Render.

## Planned
- Upload frontend to Infinity Free
- Connect Render and Infinity Free

# 30 APR 2026 MOR
## Progress
- Infinity Free registration
- Got the URL: securechat.infinityfree.me
- Connect between Infinity and Render successfully,
- Fail in authentication.

## Planned
- Upload frontend to Infinity Free
- Connect Render and Infinity Free

# 30 APR 2026 EVE
## Progress
- Creta MySQL on Infintiy Free
- Fixing bugs
- Now the user database is no longer local storage

# 1 MAY 2026 MOR
## Progress
- Fixing bugs, clean up and prepared for server.js to be compatible with client.html
- Restored missing features when move from .py to .node

## Planned
- Clean up amd make sure client.html is compatible with server.js
- Check the connections between users on different network setting (Monday testing)

# 1 MAY 2026 EVE
## Progress
- Fix and update rate limiting system, ping system
- Fixed bugs of E2EE.

## Planned
- Database stored on Firebase.

# 2 MAY 2026 MOR
## Progress
- Elimiated Firebase due to free-tier not included storage option
- Test Backblaze 
- Backblaze setting,
- Reivse new file uploading on BackblazwE

## Planned
- Clean up amd make sure client.html is compatible with server.js
- Check the connections between users on different network setting (Monday testing)

# 2 MAY 2026 EVE
## Progress
- Try to test created and chat, failed
- Connected successfuly the mySQL database on Infinity Free to Render page.
- Failed to connect to login users, have to move the DB.
- Checked pros and cons of Railway and PlanetScale

## Planned
- Move the DB to Railway DB??

# 3 MAY 2026 MOR
## Progress
- Create the tables on Railway

## Planned
- Testing and fix bugs, priority test the connections and login.

# 4 MAY 2026 EVE
## Progress
- Test the connection of the system:
 + Test register: PASSED. Fixing the read announcement "Red lines"
 + Test login: PASSED. Fix the announcement while still hide the real reason for developers only.
 + Test rate limit: PASSED

 + Trying to fix the online users issues, this come from a commented out issues. FIXED

## Planned
- Text not went through. Fix it

# 5 MAY 2026 MOR - NOON
## Progress
- Trying to fix the chat issues - FAIL

# 5 MAY 2026 EVE
## Progress
- Trying to fix the chat issues - have to wait the Infinity Free to clear cache
- Never update the file in Infinity Free is the main reason.


