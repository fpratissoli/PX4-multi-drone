import asyncio
import math
from drone_control import Drone
from drone_control import read_config

def global_to_local(global_lat, global_lon, global_alt, origin_lat, origin_lon, origin_alt=0):
    """
    Convert global coordinates to local coordinates.
    
    Args:
    global_lat, global_lon, global_alt: Global coordinates to convert
    origin_lat, origin_lon, origin_alt: Global coordinates of the origin point
    
    Returns:
    x, y, z: Local coordinates
    """
    EARTH_RADIUS = 6378137.0  # Earth's radius in meters

    d_lat = math.radians(global_lat - origin_lat)
    d_lon = math.radians(global_lon - origin_lon)
    
    lat1 = math.radians(origin_lat)
    lat2 = math.radians(global_lat)

    x = EARTH_RADIUS * d_lon * math.cos((lat1 + lat2) / 2)
    y = EARTH_RADIUS * d_lat
    z = global_alt - origin_alt

    return x, y, z

def local_to_global(local_x, local_y, local_z, origin_lat, origin_lon, origin_alt=0):
    """
    Convert local coordinates to global coordinates.
    
    Args:
    local_x, local_y, local_z: Local coordinates to convert
    origin_lat, origin_lon, origin_alt: Global coordinates of the origin point
    
    Returns:
    lat, lon, alt: Global coordinates
    """
    EARTH_RADIUS = 6378137.0  # Earth's radius in meters

    d_lat = local_y / EARTH_RADIUS
    d_lon = local_x / (EARTH_RADIUS * math.cos(math.radians(origin_lat)))

    lat = origin_lat + math.degrees(d_lat)
    lon = origin_lon + math.degrees(d_lon)
    alt = origin_alt + local_z

    return lat, lon, alt

class DroneSwarm:
    def __init__(self, config):
        self.num_drones = config['NUM_DRONES']
        self.alldrones = []
        for i in range(self.num_drones):
            i=i+1 # for 1-indexed drone numbering: PX4 when manually starting the simulation starts the server at port 50051 + 1 (px4-BUG)
            drone = Drone(i, 
                          grpc_portbase=config['GRPC_PORT_BASE'] + i,
                          connection_type=config['Connection_type'],
                          server_address=config['Server_host_address'],
                          portbase=config['Connection_port'] + i)
            self.alldrones.append(drone)

        self.origin_lat = None
        self.origin_lon = None
        self.origin_alt = None

    async def connect_swarm(self):
        await asyncio.gather(*[drone.connect() for drone in self.alldrones])

        # Set the origin to the home position of the first drone
        home = await self.alldrones[0].system.telemetry.home().__aiter__().__anext__()
        self.origin_lat = home.latitude_deg
        self.origin_lon = home.longitude_deg
        self.origin_alt = 0 #home.absolute_altitude_m
        print(f"Origin set to: {self.origin_lat}, {self.origin_lon}, {self.origin_alt}")

    async def takeoff_swarm(self):
        await asyncio.gather(*[drone.takeoff() for drone in self.alldrones])

    async def land_swarm(self):
        await asyncio.gather(*[drone.land() for drone in self.alldrones])

    async def return_swarm_to_launch(self):
        await asyncio.gather(*[drone.return_to_launch() for drone in self.alldrones])

    async def run_goto_formation(self, formation_coords):
        tasks = []
        for drone, coords in zip(self.alldrones, formation_coords):
            lat, lon, alt = coords
            tasks.append(drone.run_goto(lat, lon, alt))
        await asyncio.gather(*tasks)

    async def run_orbit_formation(self, center_lat, center_lon, radius, altitude):
        #TODO: not tested
        tasks = []
        for i, drone in enumerate(self.alldrones[:self.num_drones]):
            angle = (2 * 3.14159 * i) / self.num_drones
            lat = center_lat + (radius * 0.00001 * math.cos(angle))
            lon = center_lon + (radius * 0.00001 * math.sin(angle))
            tasks.append(drone.run_orbit(radius=5, velocity_ms=2, relative_altitude=altitude, 
                                         latitude_deg=lat, longitude_deg=lon))
        await asyncio.gather(*tasks)

    async def run_goto_local(self, local_coords):
        tasks = []
        for drone, coords in zip(self.alldrones, local_coords):
            x, y, z = coords
            lat, lon, alt = local_to_global(x, y, z, self.origin_lat, self.origin_lon, self.origin_alt)
            tasks.append(drone.run_goto(lat, lon, alt - self.origin_alt))  # alt is relative to origin
        await asyncio.gather(*tasks)

    async def run_orbit_formation_local(self, center_x, center_y, radius, altitude, num_drones):
        #TODO: not tested
        center_lat, center_lon, _ = local_to_global(center_x, center_y, 0, self.origin_lat, self.origin_lon, self.origin_alt)
        tasks = []
        for i, drone in enumerate(self.alldrones[:num_drones]):
            angle = (2 * math.pi * i) / num_drones
            x = center_x + (radius * math.cos(angle))
            y = center_y + (radius * math.sin(angle))
            lat, lon, _ = local_to_global(x, y, 0, self.origin_lat, self.origin_lon, self.origin_alt)
            tasks.append(drone.run_orbit(radius=5, velocity_ms=2, relative_altitude=altitude, 
                                         latitude_deg=lat, longitude_deg=lon))
        await asyncio.gather(*tasks)

    async def _monitor_swarm(self):
        tasks = [asyncio.ensure_future(drone._start_state_monitoring()) for drone in self.alldrones]
        await asyncio.gather(*tasks)
        print("Monitoring started")

    def print_all_internal_statuses(self):
        for drone in self.alldrones:
            drone.print_internal_status()

async def run_swarm_mission(swarm):
    await swarm.connect_swarm()
    await asyncio.sleep(4)    
    await swarm.takeoff_swarm()
    await asyncio.sleep(4)
    
    # Example formation flight
    formation_coords = [
        (47.397606, 8.543060, 20),
        (47.397706, 8.543160, 25),
        (47.397806, 8.543260, 30),
        # Add more coordinates for additional drones
    ]

    #await swarm.run_goto_formation(formation_coords)
    #await asyncio.sleep(30)

    # Example formation flight using local coordinates
    local_formation_coords = [
        (-10, 0, 20),   # 10m west, 0m north, 20m up
        (-10, 0, 30),   # 10m west, 0m north, 30m up
        (-10, 0, 40),  # 10m west, 0m north, 40m up
        # Add more coordinates for additional drones
    ]

    await swarm.run_goto_local(local_formation_coords)
    await asyncio.sleep(10)

    local_formation_coords = [
        (0, 10, 20),   # 10m east, 0m north, 20m up
        (0, 10, 30),   # 0m east, 10m north, 25m up
        (0, 10, 40),  # 10m west, 0m north, 30m up
        # Add more coordinates for additional drones
    ]

    await swarm.run_goto_local(local_formation_coords)
    await asyncio.sleep(10)
    
    # Example orbit formation
    #await swarm.run_orbit_formation(47.397606, 8.543060, 50, 30)
    #await asyncio.sleep(60)

    # Example orbit formation using local coordinates
    #await swarm.run_orbit_formation_local(0, 0, 50, 30, len(swarm.drones))
    #await asyncio.sleep(60)
    
    await swarm.return_swarm_to_launch()

    # Print coordinates of drone 0
    #asyncio.ensure_future(swarm._monitor_swarm())
    #await swarm.land_swarm()

async def main():
    config = read_config()
    swarm = DroneSwarm(config)  # Create a swarm of n drones
    swarm.print_all_internal_statuses()
    await run_swarm_mission(swarm)

if __name__ == '__main__':
    asyncio.run(main())