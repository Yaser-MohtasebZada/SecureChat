import asyncio          #multi-task server for many connections
import websockets       # websocket library //help make server communicate in real time
import ssl #to have implement TLS
import bcrypt  #not using hashlib because it use SHA256, too fast and being victimed to brute-force
import json #to save users to permanent after being hashed, because hash change every single time server reload.
import time #From MAR 9, even use for chat_logs!

# NEW PART 1: SAN + hidden server IP (Mar 6)
import os

from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import base64
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.ciphers.aead import AESGCM #MAR 14: To update like the final decision at the HTML client

mess_limit = 5 # messages
time_range = 8 # seconds
aes_session_keys = {}
"""
#MAR 9: CHAT LOGS
current_timestamp = int(time.time())
chat_log_record = f"chat_logs/chat_{current_timestamp}.txt"

def write_mess_to_log(chat_messages):
    with open(chat_log_record, "a") as log_file:
        log_file.write(chat_messages + "\n")
"""
chat_sessions = {} # MAR 10 eve: needed for the new chatfile system
#current_sessionNo = 1  #initialized as session 1, then 2,3,4 etc SINCE MAR 12, not needed anymore because numbered by pairs
active_chat_pairs = set()
#NUMBERED BY PAIR:
def get_session(user1, user2):
    users_pair = tuple(sorted([user1, user2]))

    if users_pair not in chat_sessions:
        chat_sessions[users_pair] = 1
    else: #debug session number issues [MAR 15]
        chat_sessions[users_pair] = chat_sessions[users_pair] + 1

    return chat_sessions[users_pair]

#[MAR 15: fix the numbering bug]
def start_new_session(user1, user2):
    users_pair = tuple( sorted([user1, user2]))
    chat_sessions[users_pair] = chat_sessions.get(users_pair, 0) + 1
    active_chat_pairs.discard(users_pair)

    return chat_sessions[users_pair]


#MAR 10 eve: need each chat log per session, so better chat logs are numbered
def write_mess_to_log(user1, user2, chat_message):

    users_pair = tuple(sorted([user1, user2]))

    #this pair chat the 1st time
    if users_pair not in chat_sessions: chat_sessions[users_pair] = 1

    session = chat_sessions[users_pair]
    chat_log_record = f"chat_logs/{users_pair[0]}_{users_pair[1]}_session{session}.txt"
    with open(chat_log_record, "a", encoding="utf-8") as chatlog_file:
        chatlog_file.write(chat_message + "\n")

#MAR 12: NEW DECRYPT-ENCRYPT:
"""
def encrypt_aes(key, plaintext):
    IV = os.urandom(16)
    cipher = Cipher(algorithms.AES(key), modes.CFB(IV))
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(plaintext.encode()) + encryptor.finalize()
    return base64.b64encode(IV + ciphertext).decode() #typo mismatch, fixed: MAR 13

def decrypt_aes(key, ciphertext_b64):
    raw = base64.b64decode(ciphertext_b64)
    IV, ct = raw[:16], raw[16:]
    cipher = Cipher(algorithms.AES(key), modes.CFB(IV))
    decryptor = cipher.decryptor()
    return (decryptor.update(ct) + decryptor.finalize()).decode()
"""
#MAR 14: Update to AES-GCM
def encrypt_aes(encryption_key, plain_text):
    iv = os.urandom(12)

    aesgcm = AESGCM(encryption_key)
    crypted_Text = aesgcm.encrypt(iv, plain_text.encode(), None)

    return base64.b64encode(iv + crypted_Text).decode()

def decrypt_aes(decryption_key, crypted_text_base64):
    encrypted_blob = base64.b64decode(crypted_text_base64)

    iv = encrypted_blob[:12]
    crypted_Text = encrypted_blob[12:]

    aesgcm = AESGCM(decryption_key)
    decrypted_message = aesgcm.decrypt(iv, crypted_Text, None)

    return decrypted_message.decode()

#MAR 6: SAN and hide Server IP
from dotenv import load_dotenv

load_dotenv("../.env")
IP_Of_Server = os.getenv("Server_IP")
Port_Of_Server = os.getenv("Server_Port")

# Block login (Against brute-force - MAR 7)
failed_attempts_dict = {}  # KEY: username -> VALUES: [attempt_count, last_attempt_time]

max_attemps_allowed = 3 #decided to allow 3
block_login_time = 10 #just block for 10 secs to test the code

last_pong = {} #tracking last pong message

def hash_pass(plain_pass):#hash_stored password
    return bcrypt.hashpw(plain_pass.encode(), bcrypt.gensalt())

def check_pass(plain_pass, hashed):#check password user try to log actually match with stored password
    return bcrypt.checkpw(plain_pass.encode(), hashed)


def load_users(): #load user info in user.json into memory
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
#updating users.json if needed when new user create accounts
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
clients_p_keys = {}

#[5] Check password if matched
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
#[6] heartbeat function
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
#message system 
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
    sys_log_line = f"[SYSTEM] {StCmessage}"
    #write_mess_to_log(log_line) remove it, I create new def
    write_system_log(sys_log_line)
    await server_mess(sys_log_line)
    #await server_mess(f"[SYSTEM]: {StCmessage}") #add label for the mess from servr #UPDATE TO LOG ON MAR 9

def write_system_log(message):
    with open("chat_logs/system_log.txt", "a", encoding="utf-8") as sys_log_file:
        sys_log_file.write(message + "\n")

"""
async def checking_heartbeat():
    while True: #loop forever and ever
        heartbeat_timerange = 5 #wait 5 [seconds]
        await asyncio.sleep(heartbeat_timerange)
        
        now = time.time()
        disconnected_client_set = set()

        for each_client in list(clients_connected_dict): #have to fix
            try:
                #await each_client.send("Hello!?")
                #await each_client.send("PING")
                await each_client.send(json.dumps({"type":"ping"}))
                last_time = last_pong.get(each_client)

                if last_time is not None: # Only check if we have a record for them
                    if now - last_time > 30: #increase to debug missing list of users
                        disconnected_client_set.add(each_client)
                #if now - last_pong.get(each_client, 0) > 12: #NOT RESPONSE AFTER 12 SECONDS, CLIENT IS "Dead"
                 #   disconnected_client_set.add(each_client)
            except websockets.ConnectionClosed: #if by any reason, the message is failed to be send
                disconnected_client_set.add(each_client)

        #modify dict after to avoid crash!
        for each_client in disconnected_client_set:
            username = clients_connected_dict.get(each_client, "John Doe") #get name of disconnect client, no name(!?) called as John Doe
            clients_connected_dict.pop(each_client, None) #remove that disconnected client
            last_pong.pop(each_client, None)
            clients_p_keys.pop(username, None) #remove pub key, also!
            await server_mess_wrapper(f"{username} disconnected, not listen to server!") #the verdict of server to the all system
"""

heartbeat_failures = {}

async def check_heartbeat():
    while True:
        await asyncio.sleep(12)
        to_remove = []

        for ws in list(clients_connected_dict):
            try:
                await ws.send(json.dumps({"type": "ping"}))
                heartbeat_failures[ws] = 0  
            except:
                heartbeat_failures[ws] = heartbeat_failures.get(ws, 0) + 1
                if heartbeat_failures[ws] >= 3:  #remove after 3 failures continuously
                    to_remove.append(ws)

        for ws in to_remove:
            username = clients_connected_dict.get(ws, "John Doe")
            clients_connected_dict.pop(ws, None)
            last_pong.pop(ws, None)
            clients_p_keys.pop(username, None)
            heartbeat_failures.pop(ws, None)

            active_chat_pairs_copy = set(active_chat_pairs)
            for pair in active_chat_pairs_copy:
                if username in pair:
                    active_chat_pairs.remove(pair)

            await server_mess_wrapper(f"{username} disconnected, not listen to server's heartbeat check process!")

async def file_forward(client_connectionCtS, message):
    #actually to get user name of the sender
    #sender_name = clients_connected_dict[client_connectionCtS]
    #sender_name = next((u for u, socket in clients_connected_dict.items() if socket == client_connectionCtS), None)
    sender_name = clients_connected_dict.get(client_connectionCtS)

    path_components = message.split("|")
    file_name = path_components[1]
    file_size = int(path_components[2]) #convert the size of the file in metadata STRING to be INT

    print(f"{sender_name} is sending file {file_name}")
    #write_mess_to_log(f"{sender_name} sent file: {file_name}")
    for each_client, recipient_name in clients_connected_dict.items():
        if each_client != client_connectionCtS:
            write_mess_to_log(
                sender_name,       #sender
                recipient_name,    #receiver
                #current_sessionNo, #session number Since MAR 12, not have this parameter anymore
                f"{sender_name} sent file: {file_name} ({file_size} bytes)"
            )

    # Shipping the metadata
    for each_client in clients_connected_dict:
        if each_client != client_connectionCtS: #make sure that the receiver is actually not the sender
            await each_client.send(f"file_metadata|{sender_name}|{file_name}|{file_size}")

    file_bytes = await client_connectionCtS.recv()# Receive file_bytes

    for each_client in clients_connected_dict:# Ship file bytes
        if each_client != client_connectionCtS: #re-check due to another loop
            await each_client.send(file_bytes) 

def allowed_to_try_login(username):
    now = time.time()
    if username not in failed_attempts_dict:  return True#New user is OK

    # defaule is 0 if not found
    attempt_No = failed_attempts_dict[username][0] #check the No. of fail
    last_time = failed_attempts_dict[username][1] #take the timestamp to compare

    if attempt_No < max_attemps_allowed: 
        return True #allowed
    else:
        wait_time = now - last_time
        if wait_time > block_login_time:
            failed_attempts_dict[username] = [0,0] #reset the record of that user
            return True
        else: 
            return False #not allowed


def record_failed_login(username):
    now = time.time()
    if username not in failed_attempts_dict:
        failed_attempts_dict[username] = [1, now] #first time FAIL, that attempt numbered as "1" (1ST TIME)
    else:
        failed_attempts_dict[username][0]= failed_attempts_dict[username][0] + 1 #otherwise, add 1 to the 1st value of dic, which is attemp_No
        failed_attempts_dict[username][1] = now #timestamp of the fail try go to dic

def reset_login(username): #Login successfully, then clear the record of Fail attempts
    if username in failed_attempts_dict:  del failed_attempts_dict[username]

async def handler(socket):
    username = None
    try:
        #for handsake process
        auth_mess = await socket.recv()
        try:
            data = json.loads(auth_mess)
        except json.JSONDecodeError:
            await socket.send(json.dumps({"type":"error", "message":"Invalid JSON!!!"}))
            return  ##close connection if invalid

        mess_type = data.get("type")
        username = (data.get("username") or "").strip().lower()
        passwd = (data.get("password") or "").strip()

        if not username or not passwd:
            await socket.send(json.dumps({"type":"auth_fail", "message":"Username or password is empty"}))
            return

        #Auth procesS
        if mess_type == "auth":
            if not allowed_to_try_login(username):
                await socket.send(json.dumps({
                    "type":"auth_fail",
                    "message":f"Too many failed attempts. Try again AFTER {block_login_time} seconds :("}))
                return

            if username not in registered_users or not check_pass(passwd, registered_users[username]):
                record_failed_login(username)
                await socket.send(json.dumps({"type":"auth_fail", "message":"Invalid accounts credentials."}))
                return

            reset_login(username)
            await socket.send(json.dumps({"type":"auth_success"}))

        

        #registration process
        elif mess_type == "register":
            if username in registered_users:
                await socket.send(json.dumps({"type":"auth_fail", "message":"Username already exists"}))
                return

            valid, mess = validate_password(passwd)
            if not valid:
                await socket.send(json.dumps({"type":"auth_fail", "message":mess}))
                return

            hashed = hash_pass(passwd)
            registered_users[username] = hashed
            save_users(registered_users)
            await socket.send(json.dumps({"type":"register_success"}))

        else:
            await socket.send(json.dumps({"type":"error", "message":"Lack of auth/register"}))
            return

        #after handsake
        clients_connected_dict[socket] = username
        last_pong[socket] = time.time()

        """MAR 13 Eve, remove to testing why 2 clients online but not appear in the ONLINE list in GUI
        #notify
        for other_socket in clients_connected_dict:
            if other_socket != socket:
                try:
                    await other_socket.send(json.dumps({"type":"user_joined","username":username}))
                except websockets.ConnectionClosed:
                    pass

        #provide current userlist
        await socket.send(json.dumps({"type":"user_list","users":[u for u in clients_connected_dict.values()]}))
        """
        user_list = [u for u in clients_connected_dict.values()]
        for s in clients_connected_dict:
            try:
                await s.send(json.dumps({"type":"user_list","users":user_list}))
            except websockets.ConnectionClosed:
                pass

        #HANDLE MESS - pingpong
        async for mess in socket:
            try:
                incoming_data = json.loads(mess)
            except json.JSONDecodeError:
                await socket.send(json.dumps({"type":"error","message":"Invalid JSON!"}))
                continue

            
            if incoming_data.get("type") == "pong":
                last_pong[socket] = time.time()
                continue

            if incoming_data.get("type") == "post_public_key":
                user_pub_key = incoming_data.get("key")
                clients_p_keys[username] = user_pub_key
                
                try:
                    serialization.load_pem_public_key(user_pub_key.encode())
                    clients_p_keys[username] = user_pub_key
                except Exception:
                    print(f"Invalid public key from {username}")

                #announce the new key
                await server_mess_wrapper(f"Created public key fpr {username}")

            elif incoming_data.get("type") == "message":
                if not allowed_to_send(username):
                    await socket.send(json.dumps({
                        "type":"error",
                        "message":f"Message rate exceeded ({mess_limit} per {time_range} second!!)" #rate-limiting
                    }))
                    continue

                target_user = incoming_data.get("to")
                content = incoming_data.get("content")

                #in the mean time dont allow text to offline users
                if target_user not in clients_connected_dict.values():
                    await socket.send(json.dumps({
                        "type":"error",
                        "message":"This person actually offline :("
                    }))
                    continue
                    
                users_pair = tuple(sorted([username, target_user]))
                #[NEW] encrypt mess [mar 13], cancelled MAR 14
                #aes_key = aes_session_keys.get(users_pair)
                #if aes_key:
                #    content = encrypt_aes(aes_key, content)
                content = incoming_data.get("content")

                #create new session for new pair
                #if users_pair not in active_chat_pairs:
                 #   get_session(username, target_user)
                  #  active_chat_pairs.add(users_pair)

                #check if that pair need new session number
                if users_pair not in active_chat_pairs:
                    session = start_new_session(username, target_user)
                    print(f"New chat session {session} created for {users_pair}")

                ##log_line = f"{time.strftime('%H:%M')} {username}: {content}"
                log_line = f"{time.strftime('%H:%M')} {username}: [encrypted message]" #HIDE the mess in log
                write_mess_to_log(username, target_user, log_line)

                for client_socket, uname in clients_connected_dict.items():
                    if uname == target_user:
                        await client_socket.send(json.dumps({"type":"message", "from": username,"content": content,"time": time.strftime("%H:%M")
                        }))

            #ping handling
            elif incoming_data.get("type") == "ping":
                await socket.send(json.dumps({"type":"pong"}))

            #get-user
            elif incoming_data.get("type") == "get_users":
                await socket.send(json.dumps({"type":"user_list", "users":[u for u in clients_connected_dict.values()]}))

            # file handling
            #elif incoming_data.get("type") == "file":
            #    await file_forward(socket, incoming_data.get("data")) Update raw string to JSON (mar 13)
            elif incoming_data.get("type") == "file":
                target = incoming_data.get("to")
                filename = incoming_data.get("filename")
                size = incoming_data.get("size")
                data = incoming_data.get("data")

                users_pair = tuple(sorted([username, target]))
                #encrypt file transfer [mar 13]
                #aes_key = aes_session_keys.get(users_pair)
                #if aes_key:
                #    data = encrypt_aes(aes_key, data)

                for client_socket, uname in clients_connected_dict.items():
                    if uname == target:
                        await client_socket.send(json.dumps({
                            "type":"file", "from": username, "filename": filename, 
                            "size": size, "data": data,"time": time.strftime("%H:%M")}))

            # type issues
            elif incoming_data.get("type") == "typing":
                target_user = incoming_data.get("to")
                for client_socket, uname in clients_connected_dict.items():
                    if uname == target_user:
                        await client_socket.send(json.dumps({"type":"typing", "from":username}))  

            if incoming_data.get("type") == "request_key":
                target_user = incoming_data.get("target_user")
                target_pub = clients_p_keys.get(target_user)  # recipient public key (PEM string)
                if target_pub:
                    # generate AES key for this pair
                    users_pair = tuple(sorted([username, target_user]))
                    if users_pair not in aes_session_keys:
                        aes_session_keys[users_pair] = os.urandom(32)  # AES-256
                    aes_key = aes_session_keys[users_pair]

                    # encrypt AES key with recipient's RSA public key
                    
                    pub_key_obj = serialization.load_pem_public_key(target_pub.encode())
                    enc_key = pub_key_obj.encrypt(
                        aes_key,
                        padding.OAEP(mgf=padding.MGF1(hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
                    )
                    enc_key_b64 = base64.b64encode(enc_key).decode()
                    await socket.send(json.dumps({"type":"key_response", "user":target_user, "key":enc_key_b64}))   
                    #for client_socket, uname in clients_connected_dict.items():
                     #   if uname == target_user:
                      #      await client_socket.send(json.dumps({"type":"key_response", "user": username,"key": enc_key_b64  }))   

    except websockets.ConnectionClosed:
        print(f"{username or 'Dont know who'} disconnected")
    finally:
        if socket in clients_connected_dict:
            left_user = clients_connected_dict.pop(socket)
            #remove active chat pairs of this user
            pairs_to_remove = []
            for pair in active_chat_pairs:
                if left_user in pair:
                    pairs_to_remove.append(pair)

            for pair in pairs_to_remove:
                active_chat_pairs.remove(pair)

            last_pong.pop(socket, None)
            clients_p_keys.pop(username, None)

            for other_socket in clients_connected_dict:
                try:
                    await other_socket.send(json.dumps({"type":"user_left", "username":left_user}))
                except websockets.ConnectionClosed:
                    pass

#1.main function 
async def main():

    #2. create TLS context 
    
    ssl_TLScontext = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER) 
    root_path = os.path.dirname(os.path.abspath(__file__))
    cert_abs_path = os.path.join(root_path, "../certificate/certificate.pem")
    key_abs_path = os.path.join(root_path, "../certificate/privateKey.pem")

    ssl_TLScontext.load_cert_chain(certfile=cert_abs_path, keyfile=key_abs_path)

   # ssl_TLScontext.load_cert_chain( certfile="../certificate/certificate.pem", keyfile="../certificate/privateKey.pem" ) 
    ##MUST RUN from root, because the path here will be error when run in server folder
    ##Mar 6: Update the path!

    #async, await must be in the async def
    #3.websocket run
    #async with websockets.serve( handler,port=7777,host="0.0.0.0", ssl=ssl_TLScontext): #Mar 6, change local host to 0.0.0.0 to handle all case.
    #MAR 6B: Change to .env to hide the real IP
    async with websockets.serve(handler, host="0.0.0.0", port=int(Port_Of_Server), ssl=ssl_TLScontext):
    #async with websockets.serve(handler,host="0.0.0.0", port=int(Port_Of_Server)): use IN for connect HTML and backend debugs
        print("Server is running ...")   # DEBUG WEBSOCKET
#4. Server alive by future()
         #await checking_heartbeat() server froze//
        asyncio.create_task(check_heartbeat())

        await asyncio.Future() #keep server running, freeze server, no code after this line!!!!

asyncio.run(main()) #run command to the sever


