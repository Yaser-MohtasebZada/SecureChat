import websockets
import asyncio


async def client():
    async with websockets.connect("ws://localhost:7777") as websocket: #still chose host 7777

        await websocket.send("1st Mess")
        response = await websocket.recv()

        print(response)


asyncio.run(client())