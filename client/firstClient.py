import websockets
import asyncio
import ssl #Update (Feb4 to use TLS) and import
import os #for basic file transfer attempts

"""async def send_mess(Client_Server_connection):
    while True: #asking for mess as always
        CtSmessage = input("Your message: ")
        await Client_Server_connection.send(CtSmessage) #await = wait until send mess
"""
async def auth_period(connection):


    loop = asyncio.get_running_loop() 

    while True:
        server_mess = await connection.recv()
        print(server_mess)

        if server_mess == "LOGIN SUCCESS":
            print("You can chat now!")
            break

        user_input = await loop.run_in_executor(None, input, "> ")
        await connection.send(user_input)


async def send_mess(Client_Server_connection):
    loop = asyncio.get_running_loop()

    while True:
        CtSmessage = await loop.run_in_executor(None, input, "Your message: ") #ensure that input() not crash the "while loop"
        await Client_Server_connection.send(CtSmessage)

        if CtSmessage.startswith("/file "):
                path_components = CtSmessage.split(" ", 1)
                if len(path_components) < 2:
                    print("Missing filename, do it again in next chat!!")
                    continue
                #command = path_components[0] not need, not work
                file_name = path_components[1]
                await file_sending(Client_Server_connection, file_name)
                continue
            
"""async def get_mess(Server_Client_connection):
    async for StCmessage in Server_Client_connection:
        print("\n", StCmessage)"""

async def get_mess(Server_Client_connection):
    async for comming_message_StC in Server_Client_connection:
       
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

        print(f"\n{comming_message_StC}")
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
    #1. Creat TLS Context
    ssl_TLScontext= ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT) #differ from PROTOCAL_TLS_SERVER (this one is user)
    ssl_TLScontext.load_verify_locations("certificate/certificate.pem")     #check the certificate from server
     
     #2. Connect, change ws to wss uri=Uniform Resource Identifier - how to access the file
    while True:#repeate the block, not get user out, even the connection disconnect as exeption block
        try:
            async with websockets.connect ("wss://localhost:7777" , ssl=ssl_TLScontext ) as connection: #still chose host 7777

                #await websocket.send("1st Mess OF CLIENT 1")
                #response = await websocket.recv()
            
            #print(response)
                print("Connected to server")
                #await asyncio.gather(send_mess(connection),get_mess(connection) ) #ok, send OR get mess at the mean time, only 1 fnct

                await auth_period(connection)

                await asyncio.gather(send_mess(connection), get_mess(connection))

        except Exception as Close_Reconnect:
            print("Disconnected ...")
            print("System is trying to reconnect you in 2 seconds...")
            await asyncio.sleep(2)

asyncio.run(client())