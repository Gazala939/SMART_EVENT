
import asyncio
import websockets


async def test_connection():
    url = "ws://127.0.0.1:8000/ws/events/2/availability"

    try:
        async with websockets.connect(url) as websocket:
            print("WebSocket connected successfully!")
            message = await websocket.recv()
            print("Availability received:", message)

    except Exception as error:
        print("WebSocket connection failed:")
        print(type(error).__name__, error)


asyncio.run(test_connection())
