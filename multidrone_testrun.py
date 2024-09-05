import asyncio
import math
from drone_control import Drone
from drone_control import read_config

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

    async def connect_swarm(self):
        await asyncio.gather(*[drone.connect() for drone in self.alldrones])

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

    async def monitor_swarm(self):
        #TODO: not tested
        monitoring_tasks = [drone._start_state_monitoring() for drone in self.alldrones]
        await asyncio.gather(*monitoring_tasks)

    def print_all_internal_statuses(self):
        for drone in self.alldrones:
            drone.print_internal_status()

async def run_swarm_mission(swarm):
    await swarm.connect_swarm()
    await asyncio.sleep(4)    
    await swarm.takeoff_swarm()
    await asyncio.sleep(10)
    
    # Example formation flight
    formation_coords = [
        (47.397606, 8.543060, 20),
        (47.397706, 8.543160, 25),
        (47.397806, 8.543260, 30),
        # Add more coordinates for additional drones
    ]
    await swarm.run_goto_formation(formation_coords)
    await asyncio.sleep(30)
    
    # Example orbit formation
    #await swarm.run_orbit_formation(47.397606, 8.543060, 50, 30)
    #await asyncio.sleep(60)
    
    await swarm.return_swarm_to_launch()
    await asyncio.sleep(30)

    await swarm.land_swarm()

async def main():
    config = read_config()
    swarm = DroneSwarm(config)  # Create a swarm of n drones
    swarm.print_all_internal_statuses()
    await run_swarm_mission(swarm)

if __name__ == '__main__':
    asyncio.run(main())