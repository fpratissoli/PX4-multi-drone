import drone_control
from drone_control import Drone
import asyncio
from mavsdk import System

async def start_agent(agent_id):
    drone = Drone()
    print(f"Connecting to drone {agent_id}...")
    await drone.connect()
    print(f"-- Connected to drone {agent_id}!")
    
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


async def start_swarm(num_agents):
    tasks = []
    for i in range(num_agents):
        tasks.append(asyncio.create_task(start_agent(i)))
        print(f"Started agent {i}")
    await asyncio.gather(*tasks)

async def main():
    config = drone_control.read_config()
    await start_swarm(config['NUM_DRONES'])

if __name__ == '__main__':
    asyncio.run(main())