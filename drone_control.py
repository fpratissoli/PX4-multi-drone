import asyncio
import mavsdk
from mavsdk import System
from mavsdk.action import OrbitYawBehavior
from mavsdk import telemetry
import json


def read_config():
    with open('config.json', 'r') as f:
        config = json.load(f)
    return config


class Drone:
    def __init__(self, grpc_portbase = 50051, udp_portbase = 14540):
        self.system = System(mavsdk_server_address=None, port=grpc_portbase)
        self.connection_url = f'udp://:{udp_portbase}'

    def __del__(self):
        print("agent gets destroyed")

    async def connect(self):
        print("Connecting to drone...")
        await self.system.connect(system_address=self.connection_url)
        async for state in self.system.core.connection_state():
            if state.is_connected:
                print("Drone connected!")
                break

    async def arm(self):
        print("Arming...")
        try:
            await self.system.action.arm()
        except mavsdk.ActionError as error:
            print(f"Arming failed with error code: {error._result.result}")
            print("-- Disarming")
            await self.system.action.disarm()
            await asyncio.sleep(2)
            print("-- Arming done")
            await self.system.action.arm()

    async def takeoff(self):
        #await self.connect()
        await self.arm()
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

    async def safe_land_and_disarm(self):
        print("Landing...")
        await self.system.action.land()

        #check if drone is landed
        async for landing_info in self.system.telemetry.landed_state():
            if landing_info == telemetry.LandedState.ON_GROUND:
                print("-- Drone has landed")
                break

        await self.system.action.disarm()

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
            altitude_m (float): The altitude of the target position in meters. eg. 20.0
            timeout (float): The maximum time to wait for the drone to reach the target position, in seconds. 
                If set to 0 or a negative value, the drone will not wait and will immediately return to launch.

        Returns:
            None
        """

        print("Running goto...")
        await self.connect()

        print("Waiting for drone to have a global position estimate...")
        async for health in self.system.telemetry.health():
            if health.is_global_position_ok and health.is_home_position_ok:
                print("-- Global position estimate OK")
                break

        print("Fetching amsl altitude at home location....")
        async for terrain_info in self.system.telemetry.home():
            absolute_altitude = terrain_info.absolute_altitude_m
            break

        print(f"The detected altitude at home is {absolute_altitude} m from the ground")

        print("-- Taking off")
        await self.takeoff()

        await asyncio.sleep(10)

        # To fly drone m above the ground plane
        flying_alt = absolute_altitude + altitude_m
        print(f"-- Flying to {latitude_deg}, {longitude_deg}, {flying_alt}")
        await self.system.action.goto_location(latitude_deg, longitude_deg, flying_alt, 0)

        if timeout > 0:
            print("-- Starting a timer for %s seconds" % timeout)
            await asyncio.sleep(timeout)

            print("-- Landing")
            await self.return_to_launch()

            #check if drone is landed
            async for landing_info in self.system.telemetry.landed_state():
                if landing_info == telemetry.LandedState.ON_GROUND:
                    print("-- Drone has landed")
                    break

    async def run_orbit(self, radius_m=30, velocity_ms=2, relative_altitude=10, timeout=60, latitude_deg=0, longitude_deg=0):
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
        await self.connect()

        print("Waiting for drone to have a global position estimate...")
        async for health in self.system.telemetry.health():
            if health.is_global_position_ok and health.is_home_position_ok:
                print("-- Global position estimate OK")
                break

        position = await self.system.telemetry.position().__aiter__().__anext__()
        orbit_height = position.absolute_altitude_m+relative_altitude
        yaw_behavior = OrbitYawBehavior.HOLD_FRONT_TO_CIRCLE_CENTER

        await self.takeoff()

        await asyncio.sleep(10)

        print("-- Orbiting")
        print(f"Do orbit at {orbit_height} m height from the ground")
        if latitude_deg == 0 and longitude_deg == 0:
            await self.system.action.do_orbit(radius_m=radius_m,
                                        velocity_ms=velocity_ms,
                                        yaw_behavior=yaw_behavior,
                                        latitude_deg=position.latitude_deg,
                                        longitude_deg=position.longitude_deg,
                                        absolute_altitude_m=orbit_height)
        else:
            await self.system.action.do_orbit(radius_m=radius_m,
                                        velocity_ms=velocity_ms,
                                        yaw_behavior=yaw_behavior,
                                        latitude_deg=latitude_deg,
                                        longitude_deg=longitude_deg,
                                        absolute_altitude_m=orbit_height)

        await asyncio.sleep(timeout)

        print("-- Landing")
        await self.return_to_launch()

        #check if drone is landed
        async for landing_info in self.system.telemetry.landed_state():
            if landing_info == telemetry.LandedState.ON_GROUND:
                print("-- Drone has landed")
                break

if __name__ == '__main__':
    config = read_config()
    drone = Drone(config['GRPC_PORT_BASE'], config['UDP_PORT_BASE'])

    #--- to run single operations:
    #await drone.connect()
    #await drone.arm()
    #await drone.takeoff()

    #--- to run a sequence of operations / tasks:
    #asyncio.run(drone.run_goto(47.397606, 8.543060, 20, 20))

    #--- to run an orbit mission:
    #asyncio.run(drone.run_orbit())
    #asyncio.run(drone.run_orbit(latitude_deg=47.397606, longitude_deg=8.543060))

    #--- to run a goto mission:
    asyncio.run(drone.run_goto(47.397606, 8.543060, 20, 20))

    #--- to stop the event loop
    #asyncio.get_event_loop().stop()
    #asyncio.get_event_loop().close()

    del drone