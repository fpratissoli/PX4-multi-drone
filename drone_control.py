import asyncio
import mavsdk
from mavsdk import System
from mavsdk.action import OrbitYawBehavior
from mavsdk import telemetry
import json


def read_config():
    with open('config.json', 'r') as f:
        config = json.load(f)

    if config['Connection_type'].isupper():
        config['Connection_type'] = config['Connection_type'].lower()

    if config['Connection_type'] == 'udp':
        config['Server_host_address'] = config['UDP_server_address']
        config['Connection_port'] = config['UDP_PORT_BASE']
    elif config['Connection_type'] == 'tcp':
        config['Server_host_address'] = config['TCP_server_address']
        config['Connection_port'] = config['TCP_PORT_BASE']
    elif config['Connection_type'] == 'serial':
        pass
        #TODO: Implement serial connection
    else:
        print("Invalid connection_type specified in config.json")
        # Handle the error or raise an exception
    return config

class Drone:
    def __init__(self, id, grpc_portbase=50051, connection_type='udp', server_address='', portbase=14540):
        self.id = id
        self.system = System(mavsdk_server_address=None, port=grpc_portbase)
        self.connection_url = f'{connection_type}://{server_address}:{portbase}'
        self.connection_type = connection_type
        self.server_address = server_address
        self.portbase = portbase
        self.grpc_portbase = grpc_portbase
        
        # Drone state properties
        self.is_connected = False
        self.is_armed = False
        self.in_air = False
        self.latitude = None
        self.longitude = None
        self.absolute_altitude = None
        self.relative_altitude = None
        self.home_position = None

    # getter methods -----------------------------------------------------------
    def get_connection_info(self):
        """Get the drone's connection information."""
        return {
            'connection_type': self.connection_type,
            'server_address': self.server_address,
            'portbase': self.portbase,
            'grpc_portbase': self.grpc_portbase
        }

    def get_id(self):
        """Get the drone's ID."""
        return self.id

    def get_connection_status(self):
        """Get the drone's connection status."""
        return self.is_connected

    def get_armed_status(self):
        """Get the drone's armed status."""
        return self.is_armed

    def get_flight_status(self):
        """Get the drone's in-air status."""
        return self.in_air

    def get_position(self):
        """Get the drone's current position."""
        return {
            'latitude': self.latitude,
            'longitude': self.longitude,
            'absolute_altitude': self.absolute_altitude,
            'relative_altitude': self.relative_altitude
        }

    def get_home_position(self):
        """Get the drone's home position."""
        return self.home_position
    
    async def get_coordinates(self):
        async for position in self.system.telemetry.position():
            return position.latitude_deg, position.longitude_deg, position.absolute_altitude_m, position.relative_altitude_m

    # --------------------------------------------------------------------------

    async def connect(self):
        print(f"Connecting to drone {self.id}...")
        await self.system.connect(system_address=self.connection_url)
        async for state in self.system.core.connection_state():
            if state.is_connected:
                print(f"Drone {self.id} connected!")
                self.is_connected = True
                break
        
    async def _start_state_monitoring(self, print_status=False):
        asyncio.ensure_future(self._monitor_armed(print_status))
        asyncio.ensure_future(self._monitor_in_air(print_status))
        asyncio.ensure_future(self._monitor_position(print_status))
        asyncio.ensure_future(self._monitor_home(print_status))
        print(f"Started monitoring drone {self.id} state ...")

    async def _monitor_armed(self, print_status=False):
        async for is_armed in self.system.telemetry.armed():
            self.is_armed = is_armed
            if print_status:
                print(f"Drone {self.id} armed: {is_armed}")

    async def _monitor_in_air(self, print_status=False):
        async for in_air in self.system.telemetry.in_air():
            self.in_air = in_air
            if print_status:
                print(f"Drone {self.id} in air: {in_air}")

    async def _monitor_position(self, print_status=False):
        async for position in self.system.telemetry.position():
            self.latitude = position.latitude_deg
            self.longitude = position.longitude_deg
            self.absolute_altitude = position.absolute_altitude_m
            self.relative_altitude = position.relative_altitude_m
            if print_status:
                print(f"Drone {self.id} position: ({self.latitude}, {self.longitude}, {self.absolute_altitude}, {self.relative_altitude})")

    async def _monitor_home(self, print_status=False):
        async for home in self.system.telemetry.home():
            self.home_position = home
            if print_status:
                print(f"Drone {self.id} home position: ({home.latitude_deg}, {home.longitude_deg}, {home.absolute_altitude_m})")

    async def arm(self):
        print(f"Arming drone {self.id}...")
        try:
            await self.system.action.arm()
        except mavsdk.ActionError as error:
            print(f"Arming failed with error: {error}")
            await self.disarm()
            await asyncio.sleep(2)
            await self.system.action.arm()
        else:
            self.is_armed = True

    async def takeoff(self):
        if not self.is_connected:
            await self.connect()
        await self.arm()
        print(f"Drone {self.id} taking off...")
        await self.system.action.takeoff()
        self.in_air = True
    
    async def land(self):
        print(f"Drone {self.id} landing...")
        await self.system.action.land()
        await self._wait_for_landed()
        self.in_air = False

    async def return_to_launch(self):
        print(f"Drone {self.id} returning to launch...")
        await self.system.action.return_to_launch()
        await self._wait_for_landed()
        self.in_air = False
    
    async def _wait_for_landed(self):
        async for state in self.system.telemetry.landed_state():
            if state == telemetry.LandedState.ON_GROUND:
                print(f"Drone {self.id} has landed")
                break
        
    async def disarm(self):
        print(f"Disarming drone {self.id}...")
        await self.system.action.disarm()
        self.is_armed = False
        self.in_air = False

    async def run_goto(self, latitude_deg, longitude_deg, altitude_m):
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

        # To fly drone m above the ground plane
        flying_alt = absolute_altitude + altitude_m
        print(f"Drone {self.id} flying to position...")
        await self.system.action.goto_location(latitude_deg, longitude_deg, flying_alt, 0)

    async def run_orbit(self, radius_m=30, velocity_ms=2, relative_altitude=10, latitude_deg=0, longitude_deg=0, yaw_behavior=OrbitYawBehavior.HOLD_FRONT_TO_CIRCLE_CENTER):
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

        print("Waiting for drone to have a global position estimate...")
        async for health in self.system.telemetry.health():
            if health.is_global_position_ok and health.is_home_position_ok:
                print("-- Global position estimate OK")
                break

        position = await self.system.telemetry.position().__aiter__().__anext__()
        orbit_height = position.absolute_altitude_m+relative_altitude

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

    def __str__(self):
        return (f"Drone {self.id}: Connected: {self.is_connected}, "
            f"Connection Type: {self.connection_type}, Server Address: {self.server_address}, Port Base: {self.portbase}, "
            f"gRPC Port Base: {self.grpc_portbase}, Armed: {self.is_armed}, "
            f"In Air: {self.in_air}, Position: ({self.latitude}, {self.longitude}, {self.absolute_altitude}, {self.relative_altitude}), "
            )

    def print_internal_status(self):
        print(str(self))

    async def print_status_updates(self):
        async for status in self.system.telemetry.status_text():
            print(f"Drone {self.id} status: {status.text}")

    def __del__(self):
        print(f"Drone {self.id} object is being destroyed")

# Handle Ctrl+C interrupt -----------------------------------------------------
# TODO: Implement a proper way to stop the drone when the user presses Ctrl+C
# def handle_interrupt(signal, frame):
#     print("Ctrl+C pressed. Stopping the drone...")
#     #TODO deal with stopping the drone

# signal.signal(signal.SIGINT, handle_interrupt)
# ------------------------------------------------------------------------------

async def main():
    config = read_config()
    drone = Drone(0, grpc_portbase=config['GRPC_PORT_BASE'],
                  connection_type=config['Connection_type'],
                  server_address=config['Server_host_address'],
                  portbase=config['Connection_port'])

    await drone.connect()
    # ensure_future() schedules the execution of the coroutine in the event loop - to run concurrently - to have the getter methods updated continuously
    asyncio.ensure_future(drone._start_state_monitoring()) # print_status=True to print the status continuously
    await asyncio.sleep(1)
    await drone.takeoff()
    print(drone.get_position())
    await asyncio.sleep(8)
    await drone.run_goto(47.397606, 9.543060, 20)
    await asyncio.sleep(20)
    print(drone.get_position())
    await drone.land()

    await asyncio.sleep(2)
    del drone

if __name__ == '__main__':
    #--- to run an orbit mission:
    #asyncio.run(drone.run_orbit())
    #asyncio.run(drone.run_orbit(latitude_deg=47.397606, longitude_deg=8.543060))

    #--- to run a goto mission:
    #asyncio.run(drone.run_goto(47.397606, 8.543060, 20, 20))

    #--- to stop the event loop
    #asyncio.get_event_loop().stop()
    #asyncio.get_event_loop().close()

    asyncio.run(main())