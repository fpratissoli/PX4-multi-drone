import asyncio
from mavsdk import System
from mavsdk import mission_raw

async def run():
    drone = System()
    await drone.connect(system_address="udp://:14540")

    print("Waiting for drone to connect...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print("-- Connected to drone!")
            break

    print_mission_progress_task = asyncio.ensure_future(
        print_mission_progress(drone))
    
    mission_items = []

    mission_items.append(mission_raw.MissionItem(
         0,  # start seq at 0
         6,
         16,
         1,  # first one is current
         1,
         0, 10, 0, float('nan'),
         int(47.40271757 * 10**7),
         int(8.54285027 * 10**7),
         30.0,
         0
     ))

    mission_items.append(mission_raw.MissionItem(
        1,
        6,
        16,
        0,
        1,
        0, 10, 0, float('nan'),
        int(47.40271757 * 10**7),
        int(8.54361892 * 10**7),
        30.0,
        0
    ))

    print("-- Uploading mission")
    await drone.mission_raw.upload_mission(mission_items)
    print("-- Done")

    print("Waiting for drone to have a global position estimate...")
    async for health in drone.telemetry.health():
        if health.is_global_position_ok and health.is_home_position_ok:
            print("-- Global position estimate OK")
            break

    print("-- Arming")
    await drone.action.arm()

    print("-- Starting mission")
    await drone.mission.start_mission()

    async for mission_progress in drone.mission_raw.mission_progress():
        if mission_progress.current >= mission_progress.total:
            print("-- Mission completed")
            break
        else:
            await asyncio.sleep(1)

    #print_mission_progress_task.cancel()

async def print_mission_progress(drone):
    async for mission_progress in drone.mission_raw.mission_progress():
        print(f"Mission progress: "
              f"{mission_progress.current}/"
              f"{mission_progress.total}")

if __name__ == '__main__':
    asyncio.run(run())
