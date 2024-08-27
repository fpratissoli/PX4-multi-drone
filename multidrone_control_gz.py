import asyncio
from mavsdk import System
import json

async def run():
    drone = System()
    await drone.connect(system_address="udp://:14540")

    print("Waiting for drone to be ready...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print("Drone discovered!")
            break

    print("Arming the drone...")
    await drone.action.arm()

    print("Taking off!")
    await drone.action.takeoff()

def read_json(file_name='config.json'):
    with open(file_name) as f:
        data = json.load(f)
    return data

if __name__ == "__main__":
    asyncio.ensure_future(run())
    asyncio.get_event_loop().run_forever()
