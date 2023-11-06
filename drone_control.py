#! /usr/bin/env python3

import asyncio
from mavsdk import System
from mavsdk.action import OrbitYawBehavior

class Drone:
    def __init__(self, grpc_portbase = 50041, udp_portbase = 14540):
        self.system = System(mavsdk_server_address='localhost', port=grpc_portbase)
        self.connection_url = f'udp://:{udp_portbase}'
        self.connect()

    async def connect(self):
        print("Connecting to drone...")
        await self.system.connect(system_address=self.connection_url)

    async def arm(self):
        print("Arming...")
        await self.system.action.arm()

    async def takeoff(self, altitude):
        self.arm()
        print(f"Taking off to {altitude} meters...")
        await self.system.action.takeoff()
        await asyncio.sleep(5)
        await self.system.action.goto_location(0, 0, altitude, 0)

    async def takeoff(self):
        self.arm()
        print("Taking off...")
        await self.system.action.takeoff()

    async def return_to_launch(self):
        print("Returning to launch...")
        await self.system.action.return_to_launch()

    async def land(self):
        print("Landing...")
        await self.system.action.land()

    async def disarm(self):
        print("Disarming...")
        await self.system.action.disarm()

    async def shutdown(self):
        print("Shutting down...")
        await self.system.close()

    async def print_status_text(self):
        """
        Prints the status text of the drone.

        Args:
            drone (Drone): The drone object.

        Returns:
            None
        """
        async for status in self.system.telemetry.status_text():
            print(status.text)

    async def run_orbit(self, radius, velocity, relative_altitude, timeout=60):
        print("Running orbit...")
        print("Waiting for drone to have a global position estimate...")
        async for health in self.system.telemetry.health():
            if health.is_global_position_ok and health.is_home_position_ok:
                print("-- Global position estimate OK")
                break
        
        position = await self.system.telemetry.position().__aiter__().__anext__()
        orbit_height = position.absolute_altitude_m+relative_altitude
        yaw_behavior = OrbitYawBehavior.HOLD_FRONT_TO_CIRCLE_CENTER

        await self.takeoff(orbit_height)
        
        print("-- Orbiting")
        print(f"Do orbit at {orbit_height}m height from the ground")
        await self.system.action.do_orbit(radius_m=radius,
                                    velocity_ms=velocity,
                                    yaw_behavior=yaw_behavior,
                                    latitude_deg=position.latitude_deg,
                                    longitude_deg=position.longitude_deg,
                                    absolute_altitude_m=orbit_height)
        
        await asyncio.sleep(timeout)

        print("-- Landing")
        await self.return_to_launch()
        await self.land()



if __name__ == '__main__':
    drone = Drone()
    asyncio.ensure_future(drone.takeoff())
    asyncio.get_event_loop().run_forever()