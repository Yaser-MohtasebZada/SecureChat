import websockets
import asyncio
import ssl #Update (Feb4 to use TLS)
import os #for basic file transfer attempts, MAR: now for hidden Server PORT, too

from cryptography.hazmat.primitives.asymmetric import rsa, padding #generate key pairs
from cryptography.hazmat.primitives import serialization, hashes #HASHES BEFORE rsa
from cryptography.hazmat.primitives.ciphers.aead import AESGCM #TAG-tracking system for message.
import base64 #conver raw binary for json to handle
import json

other_clients_keys = {}


def generate_RSA_key_pair():
    pr_key = rsa.generate_private_key(public_exponent=65537 #RSA parameter, not change this!!!!
    ,key_size=4096)#expected strength is 4096
    p_key = pr_key.public_key()
    return pr_key, p_key 

#COPY from server.py 
from dotenv import load_dotenv

load_dotenv("../.env")

IP_Of_Server = os.getenv("Server_IP")
Port_Of_Server = os.getenv("Server_Port")
#----------------------------------------
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


emojis_DICT = {
    ":thumbs_up:": "👍",
    ":cry:": "😢",
    ":heart:": "❤️",
    ":broken_heart:": "💔",
    ":monocle:" : "🧐",
    ":laugh:": "😆",
}

def giveout_emojis(emo_code): 
    #Replace emoji codes like :smile: with their Unicode emoji
    for emoji_unicode, emoji in emojis_DICT.items(): emo_code = emo_code.replace(emoji_unicode, emoji)
    return emo_code

"""async def send_mess(Client_Server_connection):
    while True: #asking for mess as always
        CtSmessage = input("Your message: ")
        await Client_Server_connection.send(CtSmessage) #await = wait until send mess
"""

def display_all_emojis():
    print("All emoji options")

    for emoji_unicode, emoji in emojis_DICT.items():
        print(f"{emoji_unicode} -> {emoji}", end="  ")
    print("\nType exact unicode to trade for that emoji!")

async def auth_period(connection, public_key):
    account_created = False
    username = ""
    loop = asyncio.get_running_loop()

    while True:
        server_mess = await connection.recv()
        if server_mess.startswith("Enter") or "Type R" in server_mess: #fix messing loop asking all over again
            print(server_mess)

        # using hard code to fixing bugs
        if "Enter your username" in server_mess:
            username = await loop.run_in_executor(None, input, "> ")
            await connection.send(username.strip())
            continue

        if "Enter your password" in server_mess:
            password = await loop.run_in_executor(None, input, "> ")
            await connection.send(password.strip())
            continue

        # account creation process
        if "Type R to create new account" in server_mess:
            user_choice = await loop.run_in_executor(None, input, "> ")
            await connection.send(user_choice.strip().upper())

            if user_choice.strip().upper() == "R":
                new_pass = await loop.run_in_executor(None, input, "Decide your pass: ")
                await connection.send(new_pass.strip())
                #account_created = True
                #continue
                return "NEW_USER_CREATED"
            else:
                print("Restart login....")
                continue

        if "LOGIN SUCCESS" in server_mess:
            print("You can chat now!")
            #send public keys
            public_pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            await connection.send(public_pem)
            return username.strip()
        
async def send_mess(Client_Server_connection, public_key, private_key, account_created):
    loop = asyncio.get_running_loop()

    while True:
        #CtSmessage = await loop.run_in_executor(None, input, "Your message: ") #ensure that input() not crash the "while loop"
        print("Your message: ", end="", flush=True)
        CtSmessage = await loop.run_in_executor(None, input, "")
        
        if CtSmessage.strip() == "/emoji":
            display_all_emojis()
            continue
        CtSmessage = giveout_emojis(CtSmessage)

        if CtSmessage.startswith("/file "):
                path_components = CtSmessage.split(" ", 1)
                if len(path_components) < 2:
                    print("Missing filename, do it again in next chat!!")
                    continue
                #command = path_components[0] not need, not work
                file_name = path_components[1]
                await file_sending(Client_Server_connection, file_name)
                continue
        
        #Not file, not emoji --> only a text message, then have to encrypt)
        #AES session key
        AES_key = AESGCM.generate_key(bit_length=256)
        AES_instance = AESGCM(AES_key)
        nonce = os.urandom(12)

        ciphertext = AES_instance.encrypt(nonce, CtSmessage.encode(), None)#encrypt the mess

        #encrypt AES key by RSA pub key
        receiver_key = list(other_clients_keys.values())[0]
        encrypted_AES_key = receiver_key.encrypt(
            AES_key,
            padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None )
        )

        package = {
            "sender": account_created,
            "AESkey": base64.b64encode(encrypted_AES_key).decode(),
            "nonce": base64.b64encode(nonce).decode(),
            "secret_mess": base64.b64encode(ciphertext).decode()
        }#Package for JSON and SEND
        
        await Client_Server_connection.send(json.dumps(package))
            
"""async def get_mess(Server_Client_connection):
    async for StCmessage in Server_Client_connection:
        print("\n", StCmessage)"""

async def get_mess(Server_Client_connection, private_key, account_created):
    async for comming_message_StC in Server_Client_connection:
       
        if comming_message_StC.startswith("[SYSTEM]") or "joined the chat" in comming_message_StC:
            print(f"\n{comming_message_StC}")
            print("Your message: ", end="", flush=True)
            continue
        
        if comming_message_StC.startswith("PUBLIC_KEY|"): #fix MAR 9 error in MAR 10 to store the key OF OTHERS USERS
            _, username, key_string = comming_message_StC.split("|", 2)
            other_clients_keys[username] = serialization.load_pem_public_key(key_string.encode()    ) 
            print(f"[SYSTEM] Stored public key for {username}")
            continue

        if comming_message_StC.startswith("file_metadata|"):#check the comming mess begin with file_metadata
            _, sender, file_name, file_size = comming_message_StC.split("|") 
            #take the content between the |, ignore the "file_metadata" by a underscore _
            file_bytes = await Server_Client_connection.recv()

            with open(f"received_{file_name}", "wb") as file_handler: #write-binary
                file_handler.write(file_bytes)

            print(f"Received {file_name}, {file_size}")
            continue

        if comming_message_StC == "PING":
            #await Server_Client_connection.send("Still there!!")
            await Server_Client_connection.send("PONG")
            continue
        
        try:
            #try to pasre mess as json
            recieved_package = json.loads(comming_message_StC)
            if recieved_package.get("sender") == account_created: 
                print("Your message: ", end="", flush=True)
                continue #ignore user's self message

            #extract, then decode base64 compos using keys
            encrypted_AES_key = base64.b64decode(recieved_package["AESkey"])
            nonce = base64.b64decode(recieved_package["nonce"])
            ciphertext = base64.b64decode(recieved_package["secret_mess"])

            #using RSA to decrypt AES session key
            AES_key = private_key.decrypt(
                encrypted_AES_key,
                padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None )
            )

            #AES GCM help decrypt the mess
            AES_instance = AESGCM(AES_key)
            decrypted_byte = AES_instance.decrypt(nonce, ciphertext, None)
            decrypted_mess = decrypted_byte.decode('utf-8')

            #print(f"\n[SECURE]: {decrypted_mess}")
            sender = recieved_package.get("sender", "Dont-even-know :(")
            print(f"\n[{sender}]: {decrypted_mess}")

        except json.JSONDecodeError:
            #if it's not JSON and not a system message, just print
            print(f"\n[SERVER]: {comming_message_StC}")
        
        #except (json.JSONDecodeError, KeyError):
           
         #   print(f"\n[SERVER]: {comming_message_StC}") #Deal with normal text which is not json
        
        except Exception as decryption_error:
           #if RSA key not match or data is tampered, it will happen!
            print(f"\n[ERROR]: decryption failed, send help :(. ({decryption_error})")

        #print(f"\n{comming_message_StC}")
        print("Your message: ", end="", flush=True)

async def file_sending(CtSconnection, file_name):

    if os.path.exists(file_name) == False: #check if there is a file with that name and in that category
        print("File does not exist!") 
        return #if not, STOP!

    
    file_name = os.path.basename(file_name)  # keep file name, get rid of path lead to it
    file_size = os.path.getsize(file_name) #check the size of file in terms of bytes, to limit byte size to small
    file_size_limit = 3 * 1024   # 3 KB is max. Safely not crashed, testing easier
    if file_size > file_size_limit:
        print("System cannot help you to sent the file that larger than 3 MB!")
        return
    
    # Send metadata
    await CtSconnection.send(f"file_metadata|{file_name}|{file_size}")

    # Send file bytes
    with open(file_name, "rb") as file_handler: #'rb' read + binary mode
        file_binary_style = file_handler.read() #read the content in binary mode, store in file_binary
        await CtSconnection.send(file_binary_style) #sending stream of bytes to represent the file

    print("File is sent!")

async def file_receiving(StCconnection, metadata_string):

    path_components = metadata_string.split("|")

    sender_name = path_components[1]
    file_name = path_components[2]
    file_size = int(path_components[3])

    print(f"Receiving the file named {file_name} from {sender_name}")

    #receive file bytes, then save it
    file_bytes = await StCconnection.recv()
    with open("received_" + file_name, "wb") as foreign_file:
        foreign_file.write(file_bytes)

    print("Received and stored successfully")

async def client():
    # generate key pair [MAR 8]
    pr_key, p_key = generate_RSA_key_pair()

    # 1. Create TLS Context
    ssl_TLScontext = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ssl_TLScontext.load_verify_locations("../certificate/certificate.pem")
    ssl_TLScontext.check_hostname = False
    ssl_TLScontext.verify_mode = ssl.CERT_REQUIRED

    account_created_FLAG = False


    #2. Connect, change ws to wss uri=Uniform Resource Identifier - how to access the file
    while True:  #repeate the block, not get user out, even the connection disconnect as exeption block
        try:
            #async with websockets.connect ("wss://localhost:7777" , ssl=ssl_TLScontext ) as connection: #still chose host 7777
            #MAR 6:

            async with websockets.connect(f"wss://{IP_Of_Server}:{Port_Of_Server}", ssl=ssl_TLScontext) as connection:
                #await websocket.send("1st Mess OF CLIENT 1")
                #response = await websocket.recv()
            
            #print(response)
                print("Connected to server")
                
                #await asyncio.gather(send_mess(connection),get_mess(connection) ) #ok, send OR get mess at the mean time, only 1 fnct

                #handle login
                account_created = await auth_period(connection, p_key)

                if account_created == "NEW_USER_CREATED":
                    print("Account created :D. Please reconnect.")
                    account_created_FLAG = True
                    #continue  
                    break  # stop loop after creating account
                    #await asyncio.gather(send_mess(connection, p_key, pr_key), get_mess(connection, pr_key))
                print(f"Logged in as: {account_created}. You can chat now!")
                # After successful login, run messaging tasks
                await asyncio.gather(send_mess(connection, p_key, pr_key, account_created), get_mess(connection, pr_key, account_created)
)

        except Exception as Close_Reconnect:
            if account_created_FLAG:
                break  # stop reconnect after creating account
            print("Disconnected ...")
            print(f"Connection error: {Close_Reconnect}")
            print("System is trying to reconnect you in 2 seconds...")
            await asyncio.sleep(2)

asyncio.run(client())
