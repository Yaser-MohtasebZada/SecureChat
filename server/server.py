import asyncio          #multi-task server for many connections
import websockets       # websocket library //help make server communicate in real time
import ssl #to have implement TLS

# client connect, this one runs
async def handler(websocket):
    print("client connected!")

    message = await websocket.recv() #Await: server wait mess from client while aslo can handler other tasks
    print("received: ", message)

    await websocket.send("Message is received through TLS") #Sever send mess to client

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


