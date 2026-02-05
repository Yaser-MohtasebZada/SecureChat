import websockets
import asyncio
import ssl #Update (Feb4 to use TLS)

async def client():
    #1. Creat TLS Context
    ssl_TLScontext= ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT) #differ from PROTOCAL_TLS_SERVER (this one is user)
    ssl_TLScontext.load_verify_locations("certificate/certificate.pem")     #check the certificate from server
     
     #2. Connect, change ws to wss uri=Uniform Resource Identifier - how to access the file
    async with websockets.connect ("wss://localhost:7777" , ssl=ssl_TLScontext ) as websocket: #still chose host 7777

        await websocket.send("1st Mess")
        response = await websocket.recv()

        print(response)


asyncio.run(client())