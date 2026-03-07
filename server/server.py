import asyncio          #multi-task server for many connections
import websockets       # websocket library //help make server communicate in real time
import ssl #to have implement TLS
import bcrypt  #not using hashlib because it use SHA256, too fast and being victimed to brute-force
import json #to save users to permanent after being hashed, because hash change every single time server reload.
import time
import os #to handle the hidden real IP of server.

from dotenv import load_dotenv
load_dotenv("../.env")

IP_Of_Server = os.getenv("Server_IP")
Port_Of_Server = int(os.getenv("Server_Port"))
#Coder check :D
#print("Server IP:", IP_Of_Server)
#print("Server PORT:", Port_Of_Server)

last_pong = {} #tracking last pong message
# part1: Authorize + User storage
# [1]
def hash_pass(plain_pass): #hash_stored password
    return bcrypt.hashpw(plain_pass.encode(), bcrypt.gensalt())

#[2]
def check_pass(plain_pass, hashed): #check password user try to log actually match with stored password
    return bcrypt.checkpw(plain_pass.encode(), hashed)

#[3]
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

#[4]
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
    await server_mess(f"[SYSTEM]: {StCmessage}") #add label for the mess from servr
#--------------------------------------------------------------------------------------------------------------------------------#

async def checking_heartbeat():
    while True: #loop forever and ever
        heartbeat_timerange = 5 #wait 5 [seconds]
        await asyncio.sleep(heartbeat_timerange)
        
        now = time.time()
        disconnected_client_set = set()

        for each_client in list(clients_connected_dict): #have to fix
            try:
                #await each_client.send("Hello!?")
                await each_client.send("PING")
                if now - last_pong.get(each_client, 0) > 12: #NOT RESPONSE AFTER 12 SECONDS, CLIENT IS "Dead"
                    disconnected_client_set.add(each_client)
            except websockets.ConnectionClosed: #if by any reason, the message is failed to be send
                disconnected_client_set.add(each_client)

        #modify dict after to avoid crash!
        for each_client in disconnected_client_set:
            username = clients_connected_dict.get(each_client, "John Doe") #get name of disconnect client, no name(!?) called as John Doe
            clients_connected_dict.pop(each_client, None) #remove that disconnected client
            last_pong.pop(each_client, None)
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
async def handler(client_connection):
    await client_connection.send("Enter your username:")
    username = await client_connection.recv()

    await client_connection.send("Enter your password:")
    entered_pass = await client_connection.recv()
    
    #strip the blankspaces in username and passwords
    username = username.strip().lower() #username are all lowercase per my choice
    entered_pass = entered_pass.strip()

    if username.strip() == "" or entered_pass.strip() == "": 
        #strip() clear the white space to make sure if client acidently left white sapce after/before, it is ok
        await client_connection.send("Username or password cannot be empty")
        return

    pass_in_database = registered_users.get(username) #use username as a key to find with its pair, which is real password

    """if pass_in_database is None: #this case, username not exist, so clearly no password/pair found
        await client_connection.send("Invalid username or password")
        return"""
    #elif pass_in_database != entered_pass: #the password not correct
    # check if username exists in database
    if pass_in_database is None:
        await client_connection.send("Type R to create new account with this username or L to retry login")

        user_decision = (await client_connection.recv()).strip().upper() #force the input to uppercase, also strip the blankspace
        if user_decision == "R":
            while True:
                await client_connection.send("Choose your password:")
                newuser_pass = (await client_connection.recv()).strip()

                valid, message = validate_password(newuser_pass)

                if valid: break

                await client_connection.send(message)

            hashed_password = hash_pass(newuser_pass) #hashing the pass the user just create by hash_pass()
            registered_users[username] = hashed_password

            save_users(registered_users) #save user to file by save_users()
            await client_connection.send("Account created. Connection is ended, please connect again.")
            #entered_pass = newuser_pass
            #pass_in_database = registered_users.get(username)
            return
        else:
            await client_connection.send("Restart login.")
            return
    elif check_pass(entered_pass, pass_in_database) == False:
        await client_connection.send("Invalid user or password!")
        return #to leave the program 
    else: #this case the pass that is save in database is match is password user type in
        if username in clients_connected_dict.values():
            await client_connection.send("User already logged in!")
            return
        await client_connection.send("LOGIN SUCCESS")
        print(f"{username} logged in successfully")

    """if registered_users.get(username) == password:
        await client_connection.send("Login susscefully, welcome!")
    else: 
        await client_connection.send("Fail to login!")"""

        #CHAT FUCNTION
    clients_connected_dict[client_connection] = username  #map connection to the username, track login users
    last_pong[client_connection] = time.time()

   #clients_connected_dict.add(client_connection)   #add this sepcific client connection to the set of connected clients
    print("Number of clients connected:", len(clients_connected_dict))

    #print("client connected!") 1st version, replace by system_mess
    #await server_mess_wrapper("client joined this chat")
    await server_mess_wrapper(f"{username} joined the chat")
    try:
        #while True: #this loop allow users send many mess as they want but mannually, let try to use the async let websocket handle it
         #message = await client_connection.recv() #Await: server wait mess from client while aslo can handler other tasks
         async for message in client_connection:
            if message == "PONG":
                last_pong[client_connection] = time.time()
                continue
            print("received from ", {username}, ":", message)
            if isinstance(message, str) and message.startswith("file_metadata|"):
                await file_forward(client_connection, message)
                continue
            clients_disconnected_set = set()
            '''for client in clients_connected_set:
                if client != client_connection:
                    try:
                        await client.send(message)'''
            
            sender_name = clients_connected_dict[client_connection]
            if allowed_to_send(sender_name) == False: #change position, wrong place at the last version
                await client_connection.send("Exceed the number of message amount, please wait 8 seconds!")
                #return  # Stop further processing if the user is not allowed to send the message
                #FEB 9 note: wrong :(, this kick out client --?> use continue)
                continue
            for client in clients_connected_dict:
                try: 
                    if client != client_connection:
                        await client.send(f"{sender_name}: {message}")
                except websockets.ConnectionClosed:
                         clients_disconnected_set.add(client)

            for client in clients_disconnected_set:
                clients_connected_dict.pop(client, None)  #discard is better than remove, but in dict, this funct is "pop"
         #await client_connection.send("Message is received through TLS") #Sever send mess to 1 client
            #await server_mess(message) #system now annouce to everyone 
    except websockets.ConnectionClosed:
        print("client disconnected unexpected :()")

    finally: #for anny incidents that may happeneds, client lost the connection, seens as disconnection
        #clients_connected_set.discard(client_connection) #better than remove
        #print("client disconnected!") old version
        #await server_mess_wrapper("client left this chat")
        username = clients_connected_dict.get(client_connection, "Unknown")
        clients_connected_dict.pop(client_connection, None)
        print(f"{username} disconnected")
        await server_mess_wrapper(f"{username} left the chat")



#1.main function 
async def main():

    #2. create TLS context 
    ssl_TLScontext = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER) 
    ssl_TLScontext.load_cert_chain( certfile="../certificate/certificate.pem", keyfile="../certificate/privateKey.pem" ) 
    ##MUST RUN from root, because the path here will be error when run in server folder
    ##Mar 6: Update the path!

    #async, await must be in the async def
    #3.websocket run
    #async with websockets.serve( handler,port=7777,host="0.0.0.0", ssl=ssl_TLScontext): #Mar 6, change local host to 0.0.0.0 to handle all case.
    #MAR 6B: Change to .env to hide the real IP
    async with websockets.serve(handler, host="0.0.0.0", port=Port_Of_Server, ssl=ssl_TLScontext):

        print("Server is running ...")   # hints that sever started
#4. Server alive by future()
         #await checking_heartbeat() server froze//
        asyncio.create_task(checking_heartbeat())

        await asyncio.Future() #keep server running, freeze server, no code after this line!!!!




asyncio.run(main()) #run command to the sever


