import websockets
import asyncio
import ssl #Update (Feb4 to use TLS)

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

"""async def get_mess(Server_Client_connection):
    async for StCmessage in Server_Client_connection:
        print("\n", StCmessage)"""

async def get_mess(Server_Client_connection):
    async for StCmessage in Server_Client_connection:
        print(f"\n{StCmessage}")
        print("Your message: ", end="", flush=True)

async def client():
    #1. Creat TLS Context
    ssl_TLScontext= ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT) #differ from PROTOCAL_TLS_SERVER (this one is user)
    ssl_TLScontext.load_verify_locations("certificate/certificate.pem")     #check the certificate from server
     
     #2. Connect, change ws to wss uri=Uniform Resource Identifier - how to access the file
    try:
        async with websockets.connect ("wss://localhost:7777" , ssl=ssl_TLScontext ) as connection: #still chose host 7777

            #await websocket.send("1st Mess OF CLIENT 1")
            #response = await websocket.recv()

         #print(response)
            print("Connected to server")
            #await asyncio.gather(send_mess(connection),get_mess(connection) ) #ok, send OR get mess at the mean time, only 1 fnct

            await auth_period(connection)

            await asyncio.gather(send_mess(connection), get_mess(connection))

    except Exception as Unexpected_Close:
        print("connection is closed !",  Unexpected_Close)

asyncio.run(client())