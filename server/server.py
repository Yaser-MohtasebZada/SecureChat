import asyncio          #multi-task server for many connections
import websockets       # websocket library //help make server communicate in real time
import ssl #to have implement TLS
import bcrypt  #not using hashlib because it use SHA256, too fast and being victimed to brute-force
import json #to save users to permanent after being hashed, because hash change every single time server reload.

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

# Websocket connection: client connect, this one runs
async def handler(client_connection):
    await client_connection.send("Enter your username:")
    username = await client_connection.recv()

    await client_connection.send("Enter your password:")
    entered_pass = await client_connection.recv()
    
    #strip the blankspaces in username and passwords
    username = username.strip().lower()
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

    clients_connected_dict[client_connection] = username  #map connection to the username, track login users

   #clients_connected_dict.add(client_connection)   #add this sepcific client connection to the set of connected clients
    print("Dictonary of clients connected:", len(clients_connected_dict))

    #print("client connected!") 1st version, replace by system_mess
    #await server_mess_wrapper("client joined this chat")
    await server_mess_wrapper(f"{username} joined the chat")
    try:
        #while True: #this loop allow users send many mess as they want but mannually, let try to use the async let websocket handle it
         #message = await client_connection.recv() #Await: server wait mess from client while aslo can handler other tasks
         async for message in client_connection:
            print("received: ", message)
            clients_disconnected_set = set()
            '''for client in clients_connected_set:
                if client != client_connection:
                    try:
                        await client.send(message)'''
            
            sender_name = clients_connected_dict[client_connection]

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
    ssl_TLScontext.load_cert_chain( certfile="certificate/certificate.pem", keyfile="certificate/privateKey.pem" ) 
    ##MUST RUN from root, because the path here will be error when run in server folder

    #async, await must be in the async def
    #3.websocket run
    async with websockets.serve( handler,port=7777,host="localhost", ssl=ssl_TLScontext):

        print("Server is running ...")   # hints that sever started
#4. Server alive by future()
        await asyncio.Future() #keep server running



asyncio.run(main()) #run command to the sever


