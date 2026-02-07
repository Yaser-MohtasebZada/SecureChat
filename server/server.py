import asyncio          #multi-task server for many connections
import websockets       # websocket library //help make server communicate in real time
import ssl #to have implement TLS

#IMPORTANT: multi-connect neeed to be outside fucnts, act globally
#clients_connected_set = set() replace becaue want to know NAME of client
clients_connected_dict = {} #store name of client

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
        clients_connected_dict.discard(each_client)

async def server_mess_wrapper(StCmessage):
    await server_mess(f"[SYSTEM]: {StCmessage}") #add label for the mess from servr

# Websocket connection: client connect, this one runs
async def handler(client_connection):
    await client_connection.send("Enter your username:")
    username = await client_connection.recv()

    clients_connected_dict[client_connection] = username

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
                clients_connected_dict.discard(client)
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


