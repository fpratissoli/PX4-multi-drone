#!/usr/bin/env python3

import asyncio
from mavsdk import System

async def main():
    drone = System()
    await drone.connect()

    status_text_task = asyncio.ensure_future(print_status_text(drone))
    
    print("Waiting for drone to connect...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print(f"-- Connected to drone!")
            break
    
    print("Waiting for drone to have a global position estimate...")
    async for health in drone.telemetry.health():
        if health.is_global_position_ok and health.is_home_position_ok:
            print("-- Global position estimate OK")
            break

    await drone.action.arm()
    print("Arming")
    await drone.action.takeoff()
    print("Taking off")

    await asyncio.sleep(10)

    await drone.action.land()
    print("Landing")

    status_text_task.cancel()

async def print_status_text(drone):
    async for status in drone.telemetry.status_text():
        print(status.text)

if __name__ == '__main__':
    asyncio.run(main())