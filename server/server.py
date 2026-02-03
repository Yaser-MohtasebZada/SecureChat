import asyncio          
import websockets       # websocket library //help make server

# client connect, this one runs
async def handler(websocket):
    print("Client connected")   # Mess that clearly shows that client connect successfully


# main function 
async def main():

    # create websocket server  
    async with websockets.serve(handler, "localhost", 7777):

        print("Server is running ...")   # hints that sever started

        await asyncio.Future() #keep server running

async def handler(websocket):
    print("client connected!")

    message = await websocket.recv()
    print("received: ", message)

    await websocket.send("Message is received")

asyncio.run(main())
