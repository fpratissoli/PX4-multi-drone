#! /usr/bin/env python3

import asyncio
from mavsdk import System
from mavsdk.action import OrbitYawBehavior

async def my_coroutine():
    # Your code here
    await asyncio.sleep(1)

async def main():
    drone = System()
    await drone.connect()

    print("Waiting for drone to connect...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print("Drone discovered!")
            break

    print("Waiting for drone to have a global position estimate...")
    async for health in drone.telemetry.health():
        if health.is_global_position_ok and health.is_home_position_ok:
            print("-- Global position estimate OK")
            break

    position = await drone.telemetry.position().__aiter__().__anext__()
    orbit_height = position.absolute_altitude_m+10
    yaw_behavior = OrbitYawBehavior.HOLD_FRONT_TO_CIRCLE_CENTER

    print("-- Arming")
    await drone.action.arm()

    print("-- Taking off")
    await drone.action.takeoff()

    await asyncio.sleep(10)

    print("-- Orbiting")
    print("Do orbit at 10m height from the ground")
    print("orbit_height: ", orbit_height)
    await drone.action.do_orbit(radius_m=10,
                                velocity_ms=2,
                                yaw_behavior=yaw_behavior,
                                latitude_deg=47.398036222362471,
                                longitude_deg=8.5450146439425509,
                                absolute_altitude_m=orbit_height)
    
    await asyncio.sleep(60)

    print("-- Landing")
    await drone.action.return_to_launch()

if __name__ == '__main__':
    asyncio.run(main())

