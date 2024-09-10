import asyncio
from mavsdk import System
import subprocess
import os

MAVSDK_SERVER_PATH = os.environ.get('MAVSDK_SERVER_PATH')
GRPC_PORT_BASE = 50041
UDP_PORT_BASE = 14541
NUM_AGENTS = 2

def run_mavsdk_servers(num_agents):
    mavsdk_server = os.path.join('../', MAVSDK_SERVER_PATH, 'mavsdk_server')
    mavsdk_servers = []
    for i in range(num_agents):
        mavsdk_process = subprocess.Popen([mavsdk_server, '-p', str(GRPC_PORT_BASE + i), f'udp://:{UDP_PORT_BASE + i}'])
        mavsdk_servers.append(mavsdk_process)
        print(f"Started mavsdk_server {i} on ports {GRPC_PORT_BASE + i} and {UDP_PORT_BASE + i}")

    return mavsdk_servers

def stop_mavsdk_servers(mavsdk_servers):
    for mavsdk_process in mavsdk_servers:
        mavsdk_process.terminate()

async def start_agent(agent_id):
    drone = System(mavsdk_server_address='localhost', port=GRPC_PORT_BASE + agent_id)
    print(f"Connecting to drone {agent_id}...")
    await drone.connect(system_address=f'udp://:{UDP_PORT_BASE + agent_id}')

    status_text_task = asyncio.ensure_future(print_status_text(drone))

    print(f"Waiting for drone {agent_id} to connect...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print(f"-- Connected to drone {agent_id}!")
            break

    print(f"Waiting for drone {agent_id} to have a global position estimate...")
    async for health in drone.telemetry.health():
        if health.is_global_position_ok and health.is_home_position_ok:
            print(f"-- Global position estimate OK")
            break


    await drone.action.arm()
    print(f"Arming drone {agent_id}")
    await drone.action.takeoff()
    print(f"Taking off drone {agent_id}")

    await asyncio.sleep(10)

    await drone.action.land()
    print(f"Landing drone {agent_id}")

    status_text_task.cancel()

async def stop_agent(drone):
    await drone.action.land()
    print(f"Landing drone {drone}")

async def start_swarm(num_agents):
    tasks = []
    for i in range(num_agents):
        tasks.append(asyncio.create_task(start_agent(i)))
        print(f"Started agent {i}")
    await asyncio.gather(*tasks)

async def stop_swarm(drones):
    for drone in drones:
        await stop_agent(drone)

async def print_status_text(drone):
    """
    Prints the status text of the drone.

    Args:
        drone (Drone): The drone object.

    Returns:
        None
    """
    async for status in drone.telemetry.status_text():
        print(status.text)

async def main():
    mavsdk_servers = run_mavsdk_servers(NUM_AGENTS)
    await start_swarm(NUM_AGENTS)
    #await asyncio.sleep(10)
    #await stop_swarm(drones)
    stop_mavsdk_servers(mavsdk_servers)

if __name__ == "__main__":
    asyncio.run(main())
