#! /usr/bin/env python3

import asyncio
from mavsdk import System
from mavsdk.action import OrbitYawBehavior

class Drone:
    def __init__(self, grpc_portbase = 50041, udp_portbase = 14540):
        self.system = System(mavsdk_server_address='localhost', port=grpc_portbase)
        self.connection_url = f'udp://:{udp_portbase}'

    async def connect(self):
        print("Connecting to drone...")
        await self.system.connect(system_address=self.connection_url)

    async def arm(self):
        await self.connect()
        print("Arming...")
        await self.system.action.arm()

    async def takeoff(self, altitude):
        await self.arm()
        print(f"Taking off to {altitude} meters...")
        await self.system.action.takeoff()
        await asyncio.sleep(5)
        await self.system.action.goto_location(0, 0, altitude, 0)

    async def takeoff(self):
        await self.arm()
        print("Taking off...")
        await self.system.action.takeoff()

    async def return_to_launch(self):
        print("Returning to launch...")
        await self.system.action.return_to_launch()

    async def land(self):
        print("Landing...")
        await self.system.action.land()

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

    
    async def run_goto(self, latitude_deg, longitude_deg, altitude_m, timeout=60):
        """
        Commands the drone to fly to a specified global position and altitude.

        Args:
            latitude_deg (float): The latitude of the target position in degrees. eg. 47.397606 
            longitude_deg (float): The longitude of the target position in degrees. eg. 8.543060
            altitude_m (float): The altitude of the target position in meters.
            timeout (float): The maximum time to wait for the drone to reach the target position, in seconds. 
                If set to 0 or a negative value, the drone will not wait and will immediately return to launch.

        Returns:
            None
        """
        print("Running goto...")
        print("Waiting for drone to have a global position estimate...")
        async for health in self.system.telemetry.health():
            if health.is_global_position_ok and health.is_home_position_ok:
                print("-- Global position estimate OK")
                break

        print("-- Taking off")
        await self.takeoff()

        print("-- Going to first point")
        await self.system.action.goto_location(latitude_deg, longitude_deg, altitude_m, 0)

        if timeout > 0:
            print("-- Starting a timer for %s seconds" % timeout)
            await asyncio.sleep(timeout)

            print("-- Landing")
            await self.return_to_launch()
    
    async def run_orbit(self, radius_m=10, velocity_ms=2, relative_altitude=10, timeout=60):
        """
        Runs an orbit mission for the drone.

        Args:
            radius_m (float): The radius of the orbit in meters.
            velocity_ms (float): The velocity of the drone in meters per second.
            relative_altitude (float): The relative altitude of the drone in meters.
            timeout (float): The maximum time to run the mission in seconds.

        Returns:
            None
        """
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
        await self.system.action.do_orbit(radius_m=radius_m,
                                    velocity_ms=velocity_ms,
                                    yaw_behavior=yaw_behavior,
                                    latitude_deg=position.latitude_deg,
                                    longitude_deg=position.longitude_deg,
                                    absolute_altitude_m=orbit_height)
        
        await asyncio.sleep(timeout)

        print("-- Landing")
        await self.return_to_launch()
        #await self.land()



if __name__ == '__main__':
    drone = Drone()
    #---to run single operations:
    #await drone.connect()
    #await drone.arm()
    #await drone.takeoff()

    #---to run a sequence of operations / tasks:
    #asyncio.run(drone.run_orbit())

    #asyncio.ensure_future(drone.run_orbit())
    #asyncio.get_event_loop().run_forever()