import asyncio          #multi-task server for many connections
import websockets       # websocket library //help make server communicate in real time
import ssl #to have implement TLS
import bcrypt  #not using hashlib because it use SHA256, too fast and being victimed to brute-force
import json #to save users to permanent after being hashed, because hash change every single time server reload.
import time

def is_json(raw):
    """Returns parsed dict if message is JSON, else None."""
    try:
        return json.loads(raw)
    except:
        return None 

def hash_pass(plain_pass):
    return bcrypt.hashpw(plain_pass.encode(), bcrypt.gensalt())

def check_pass(plain_pass, hashed):
    return bcrypt.checkpw(plain_pass.encode(), hashed)

def load_users():
    try:
        with open("users.json", "r") as file: #"with" - close file after 'r'-read only mode
            dataPython = json.load(file) #read from json file, convert to Python dictionary

            users_dict = {} #create user dict

            for each_user in dataPython:
                stored_hashed_pass = dataPython[each_user]
                users_dict[each_user] = stored_hashed_pass.encode() #encode(): covert string to bytes, decode() for convert bytes to string

        return users_dict 
    except FileNotFoundError:
        return {}

"""
registered_users = { 
    #testing list of user by format username:password; TESTING on plaintext
    #update Feb8: use hash funct above to hased the pass
    "alice": hash_pass("----"),
    "bob": hash_pass("----"),
    "oscar": hash_pass("----"),
    "carlos": hash_pass("-----")
}"""
registered_users = load_users()

def save_users(users_list_dict):
    json_style_data = {} #create empty dict

    for each_username in users_list_dict:
        hashed_pass_bytes = users_list_dict[each_username] #using username to get its pair/value in userlistdict (hased pass)
        hashed_pass_string = hashed_pass_bytes.decode() #convert back bytes to string by decode() for JSON
        json_style_data[each_username] = hashed_pass_string #store hash pass in file

    with open("users.json", "w") as usersJSON_file:#better version, file close safely
        json.dump(json_style_data, usersJSON_file)

    #usersJSON_file = open("users.json", "w") #open file, then "w" for write in file
    #json.dump(json_style_data, usersJSON_file) #save in json file
    #usersJSON_file.close() #close json file

#IMPORTANT: multi-connect neeed to be outside fucnts, act globally
#clients_connected_set = set() replace becaue want to know NAME of client
clients_connected_dict = {} #store name of client

def validate_password(password):
    if len(password) < 8:
        return False, "8 characters password is required"

    has_upper = False
    has_lower = False
    has_digit = False

    for char in password:
        if char.isupper():has_upper = True
        elif char.islower():has_lower = True
        elif char.isdigit(): has_digit = True

    if has_upper == False:return False, "Uppercase letter is required"
    if has_lower== False: return False, "Lowercase letter is required"
    if has_digit == False: return False, "At least one number is required"

    return True, "Password is valid"

"""
async def system_announcement(system_Message):
    client_disconnected_set = set()  #create the list of diconnected clients

    for each_client in clients_connected_set: #each client in connected list recieve sys-announce
        try:
            await each_client.send(system_Message)
        except websockets.exceptions.ConnectionClosed: #but if that client disconnect, add them to the list/set
            client_disconnected_set.add(each_client)

    # Remove disconnected clients
    for each_client in client_disconnected_set:
        clients_connected_set.discard(each_client)
  """



user_timestamp_dict = {}   # KEY: username -> PAIR VALUE: timestamps

#valid_timestamps = []

def allowed_to_send(username):
    now = time.time()
    if username not in user_timestamp_dict:
        user_timestamp_dict[username] = []

    # Get the list of timestamps for this user
    user_timestamps = user_timestamp_dict[username]

    # Create a list to hold the valid timestamps within the time window
    valid_timestamps = []

    # Loop through each timestamp, check NOW - oldtimestamp < 10 (seconds), if within, add to the VALID-list
    for each_timestamp in user_timestamps:
        if now - each_timestamp < time_range: 
            valid_timestamps.append(each_timestamp)

    #dinished the loop, assigned a whole list of VALID-timestamp to be values of the KEY:username in that dict
    user_timestamp_dict[username] = valid_timestamps

    #check the length (number of) timestamp to dertermine HOW MANY messange and if that exceed the requirements, yet(!>)
    if len(valid_timestamps) >= mess_limit:
        return False  #Exceed the limit

    # Ok, "NOW" and the order of NOW-message is accepted, "NOW"-timestamp added to the list dict
    user_timestamp_dict[username].append(now)
    return True

async def server_mess(StCmessage):
    clients_disconnected_set = set()

    #for each_client in clients_connected_set:
    for each_client in clients_connected_dict:
        try:
            await each_client.send(StCmessage)
        except websockets.exceptions.ConnectionClosed:
            clients_disconnected_set.add(each_client)

    for each_client in clients_disconnected_set:
        clients_connected_dict.pop(each_client, None)

async def server_mess_wrapper(StCmessage):
    await server_mess(f"[SYSTEM]: {StCmessage}") #add label for the mess from servr

async def checking_heartbeat():
    while True: #loop forever and ever
        heartbeat_timerange = 12 #wait 12 [seconds]
        await asyncio.sleep(heartbeat_timerange)

        disconnected_client_set = set()

        for each_client in clients_connected_dict:
            try:
                #await each_client.send("Hello!?")
                await each_client.send("PING")
            except websockets.ConnectionClosed: #if by any reason, the message is failed to be send
                disconnected_client_set.add(each_client)

        #modify dict after to avoid crash!
        for each_client in disconnected_client_set:
            username = clients_connected_dict.get(each_client, "John Doe") #get name of disconnect client, no name(!?) called as John Doe
            clients_connected_dict.pop(each_client, None) #remove that disconnected client
            await server_mess_wrapper(f"{username} disconnected, not listen to server!") #the verdict of server to the all system

async def file_forward(client_connectionCtS, message):
    #actually to get user name of the sender
    sender_name = clients_connected_dict[client_connectionCtS]

    path_components = message.split("|")
    file_name = path_components[1]
    file_size = int(path_components[2]) #convert the size of the file in metadata STRING to be INT

    print(f"{sender_name} is sending file {file_name}")

    # Shipping the metadata
    for each_client in clients_connected_dict:
        if each_client != client_connectionCtS: #make sure that the receiver is actually not the sender
            await each_client.send(f"file_metadata|{sender_name}|{file_name}|{file_size}")

    file_bytes = await client_connectionCtS.recv()# Receive file_bytes

    for each_client in clients_connected_dict:# Ship file bytes
        if each_client != client_connectionCtS: #re-check due to another loop
            await each_client.send(file_bytes) 

mess_limit = 5 # messages
time_range = 8 # seconds
# Websocket connection: client connect, this one runs
def is_json(raw):
    # Try to parse the message as JSON
    # If it works, return the parsed dict
    # If it fails (plain text terminal message), return None
    try:
        return json.loads(raw)
    except:
        return None

async def handle_gui(client_connection, first_msg):
    # Mark this connection as a GUI client so other parts of the code know
    client_connection._gui = True
    last_pong[client_connection] = time.time()

    # Pull out the fields from the JSON auth message
    msg_type = first_msg.get("type")           # "login" or "register"
    username  = first_msg.get("username", "").strip().lower()
    password  = first_msg.get("password", "")

    # Reject if either field is empty
    if not username or not password:
        await client_connection.send(json.dumps({"type": "auth_fail", "message": "Username and password required"}))
        return

    # ── REGISTER ────────────────────────────────────────────────────────────
    if msg_type == "register":
        # Check if username is already taken
        if username in registered_users:
            await client_connection.send(json.dumps({"type": "auth_fail", "message": "Username already taken"}))
            return
        # Check password meets requirements (length, upper, lower, digit)
        valid, vmsg = validate_password(password)
        if not valid:
            await client_connection.send(json.dumps({"type": "auth_fail", "message": vmsg}))
            return
        # Hash and save the new user
        registered_users[username] = hash_pass(password)
        save_users(registered_users)
        await client_connection.send(json.dumps({"type": "auth_success"}))
        print(f"{username} registered (GUI)")

    # ── LOGIN ────────────────────────────────────────────────────────────────
    elif msg_type == "login":
        # Block if too many failed attempts (brute force protection)
        if not allowed_to_try_login(username):
            await client_connection.send(json.dumps({"type": "auth_fail", "message": "Too many failed attempts. Wait 30s."}))
            return
        # Check username exists and password matches
        stored = registered_users.get(username)
        if stored is None or not check_pass(password, stored):
            record_failed_login(username)  # count this as a failed attempt
            await client_connection.send(json.dumps({"type": "auth_fail", "message": "Invalid username or password"}))
            return
        # Prevent the same user logging in twice at the same time
        if username in clients_connected_dict.values():
            await client_connection.send(json.dumps({"type": "auth_fail", "message": "User already logged in"}))
            return
        # Login success — clear any failed attempt record
        reset_login(username)
        await client_connection.send(json.dumps({"type": "auth_success"}))
        print(f"{username} logged in (GUI)")

    # ── AUTHENTICATED — add to connected users ───────────────────────────────
    clients_connected_dict[client_connection] = username
    last_pong[client_connection] = time.time()
    write_mess_to_log(f"[SYSTEM] {username} joined the chat")
    print("Number of clients connected:", len(clients_connected_dict))

    # Tell every other connected client that this user joined
    for ws in list(clients_connected_dict.keys()):
        if ws != client_connection:
            if getattr(ws, '_gui', False):
                # GUI clients get a JSON message
                await ws.send(json.dumps({"type": "user_joined", "username": username}))
            else:
                # Terminal clients get a plain text announcement
                try: await ws.send(f"[SYSTEM] {username} joined the chat")
                except: pass

    # Send this new client the full list of currently online users
    # so their sidebar populates immediately
    await client_connection.send(json.dumps({
        "type": "user_list",
        "users": list(clients_connected_dict.values())
    }))

    # ── MESSAGE LOOP — keep listening until client disconnects ───────────────
    try:
        async for raw in client_connection:
            # Any message counts as proof the client is still alive
            last_pong[client_connection] = time.time()

            # Ignore plain PONG heartbeat replies
            if raw == "PONG":
                continue

            # Parse the incoming JSON message
            msg = is_json(raw)
            if not msg:
                continue  # ignore anything that isn't valid JSON

            mtype = msg.get("type", "")

            # ── PING — client checking connection is alive ───────────────────
            if mtype == "ping":
                await client_connection.send(json.dumps({"type": "pong"}))
                continue

            # ── GET USERS — client requesting fresh user list ────────────────
            if mtype == "get_users":
                await client_connection.send(json.dumps({
                    "type": "user_list",
                    "users": list(clients_connected_dict.values())
                }))
                continue

            # ── TYPING — forward typing indicator to the target user ─────────
            if mtype == "typing":
                target = msg.get("to", "")
                for ws, uname in clients_connected_dict.items():
                    if uname == target and getattr(ws, '_gui', False):
                        await ws.send(json.dumps({"type": "typing", "from": username}))
                continue

            # ── MESSAGE — forward a chat message to the target user ──────────
            if mtype == "message":
                # Check rate limit before doing anything
                if not allowed_to_send(username):
                    await client_connection.send(json.dumps({"type": "rate_limit"}))
                    continue
                target  = msg.get("to", "")
                content = msg.get("content", "")
                if not content:
                    continue
                t = time.strftime("%H:%M")
                write_mess_to_log(f"[{t}] {username} -> {target}: {content}")
                # Find the target user and deliver the message only to them
                for ws, uname in list(clients_connected_dict.items()):
                    if uname == target and getattr(ws, '_gui', False):
                        await ws.send(json.dumps({
                            "type": "message",
                            "from": username,
                            "content": content,
                            "time": t
                        }))
                continue

            # ── FILE — forward a file transfer to the target user ────────────
            if mtype == "file":
                # Check rate limit before doing anything
                if not allowed_to_send(username):
                    await client_connection.send(json.dumps({"type": "rate_limit"}))
                    continue
                target   = msg.get("to", "")
                filename = msg.get("filename", "file")
                size     = msg.get("size", 0)
                data     = msg.get("data", "")  # base64 encoded file contents
                t = time.strftime("%H:%M")
                write_mess_to_log(f"[{t}] {username} sent file '{filename}' to {target}")
                # Find the target user and deliver the file only to them
                for ws, uname in list(clients_connected_dict.items()):
                    if uname == target and getattr(ws, '_gui', False):
                        await ws.send(json.dumps({
                            "type": "file",
                            "from": username,
                            "filename": filename,
                            "size": size,
                            "data": data,
                            "time": t
                        }))
                continue

    except websockets.ConnectionClosed:
        print("client disconnected unexpected (GUI)")

    finally:
        # Always runs — clean up whether disconnect was clean or not
        uname = clients_connected_dict.pop(client_connection, "Unknown")
        last_pong.pop(client_connection, None)
        write_mess_to_log(f"[SYSTEM] {uname} left the chat")
        print(f"{uname} disconnected (GUI)")
        # Tell all remaining clients this user left
        for ws in list(clients_connected_dict.keys()):
            if getattr(ws, '_gui', False):
                try: await ws.send(json.dumps({"type": "user_left", "username": uname}))
                except: pass
            else:
                try: await ws.send(f"[SYSTEM] {uname} left the chat")
                except: pass


async def handle_terminal(client_connection, first_raw):
    last_pong[client_connection] = time.time()
    # Mark this as a terminal client (not GUI)
    client_connection._gui = False

    # first_raw is already the username — the handler received it before calling us
    # so we do NOT call recv() again here, just use what was passed in
    username = first_raw.strip().lower()

    await client_connection.send("Enter your password:")
    entered_pass = (await client_connection.recv()).strip()

    # Reject empty fields
    if username == "" or entered_pass == "":
        await client_connection.send("Username or password cannot be empty")
        return

    pass_in_database = registered_users.get(username)

    # ── Username not found — offer to register ───────────────────────────────
    if pass_in_database is None:
        await client_connection.send("Type R to create new account with this username or L to retry login")
        user_decision = (await client_connection.recv()).strip().upper()
        if user_decision == "R":
            # Keep asking until password meets requirements
            while True:
                await client_connection.send("Choose your password:")
                newuser_pass = (await client_connection.recv()).strip()
                valid, message = validate_password(newuser_pass)
                if valid: break
                await client_connection.send(message)
            # Hash and save the new user then disconnect so they reconnect fresh
            hashed_password = hash_pass(newuser_pass)
            registered_users[username] = hashed_password
            save_users(registered_users)
            await client_connection.send("Account created. Connection is ended, please connect again.")
            return
        else:
            await client_connection.send("Restart login.")
            return

    # ── Wrong password ───────────────────────────────────────────────────────
    elif check_pass(entered_pass, pass_in_database) == False:
        record_failed_login(username)  # track failed attempt for brute force protection
        await client_connection.send("Invalid user or password!")
        return

    # ── Correct password ─────────────────────────────────────────────────────
    else:
        # Prevent same user logging in twice
        if username in clients_connected_dict.values():
            await client_connection.send("User already logged in!")
            return
        await client_connection.send("LOGIN SUCCESS")
        reset_login(username)  # clear any previous failed attempt record
        print(f"{username} logged in successfully (terminal)")

    # ── AUTHENTICATED — add to connected users ───────────────────────────────
    clients_connected_dict[client_connection] = username
    last_pong[client_connection] = time.time()
    print("Number of clients connected:", len(clients_connected_dict))
    await server_mess_wrapper(f"{username} joined the chat")

    # Also notify any GUI clients that a terminal user joined
    for ws in list(clients_connected_dict.keys()):
        if ws != client_connection and getattr(ws, '_gui', False):
            try: await ws.send(json.dumps({"type": "user_joined", "username": username}))
            except: pass

    # ── MESSAGE LOOP — keep listening until client disconnects ───────────────
    try:
        async for message in client_connection:
            # Heartbeat reply — update last seen time and skip
            if message == "PONG":
                last_pong[client_connection] = time.time()
                continue

            print("received from", username, ":", message)

            # File transfer — hand off to the existing file_forward function
            if isinstance(message, str) and message.startswith("file_metadata|"):
                await file_forward(client_connection, message)
                continue

            clients_disconnected_set = set()

            # Check rate limit
            sender_name = clients_connected_dict[client_connection]
            if not allowed_to_send(sender_name):
                await client_connection.send("Exceed the number of message amount, please wait 8 seconds!")
                continue

            # Broadcast to all other connected clients
            for client in clients_connected_dict:
                try:
                    if client != client_connection:
                        await client.send(f"{sender_name}: {message}")
                except websockets.ConnectionClosed:
                    # If a client dropped, mark it for cleanup
                    clients_disconnected_set.add(client)

            # Clean up any clients that dropped during broadcast
            for client in clients_disconnected_set:
                clients_connected_dict.pop(client, None)

    except websockets.ConnectionClosed:
        print("client disconnected unexpected :()")

    finally:
        # Always runs — clean up whether disconnect was clean or not
        username = clients_connected_dict.get(client_connection, "Unknown")
        clients_connected_dict.pop(client_connection, None)
        last_pong.pop(client_connection, None)
        print(f"{username} disconnected (terminal)")
        await server_mess_wrapper(f"{username} left the chat")
        # Also notify any GUI clients that this terminal user left
        for ws in list(clients_connected_dict.keys()):
            if getattr(ws, '_gui', False):
                try: await ws.send(json.dumps({"type": "user_left", "username": username}))
                except: pass


async def handler(client_connection):
    # This is the entry point for every new connection
    # We peek at the very first message to decide what kind of client this is
    last_pong[client_connection] = time.time()
    try:
        first_raw = await asyncio.wait_for(client_connection.recv(), timeout=30)
    except asyncio.TimeoutError:
        # Client connected but never sent anything — drop it
        return

    first_msg = is_json(first_raw)

    if first_msg and first_msg.get("type") in ("login", "register"):
        # First message was JSON with type login/register → browser GUI client
        await handle_gui(client_connection, first_msg)
    else:
        # First message was plain text (the username) → terminal client
        await handle_terminal(client_connection, first_raw)


#1.main function
async def main():

    #2. create TLS context 
    ssl_TLScontext = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER) 
    ssl_TLScontext.load_cert_chain( certfile="certificate/certificate.pem", keyfile="certificate/privateKey.pem" ) 
    ##MUST RUN from root, because the path here will be error when run in server folder

    #async, await must be in the async def
    #3.websocket run
    async with websockets.serve( handler,port=7777,host="localhost", ssl=ssl_TLScontext):

        print("Server is running ...")   # hints that sever started
#4. Server alive by future()
         #await checking_heartbeat() server froze//
        asyncio.create_task(checking_heartbeat())

        await asyncio.Future() #keep server running, freeze server, no code after this line!!!!




asyncio.run(main()) #run command to the sever


