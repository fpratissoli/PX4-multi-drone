import asyncio
from mavsdk import System
from mavsdk.mission import (MissionItem, MissionPlan)

async def run():
    drone = System()
    await drone.connect(system_address="udp://:14540")

    print("waiting for drone to connect...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print(f"drone discovered!")
            break

    print_mission_progress_task = asyncio.ensure_future(
        print_mission_progress(drone))

    running_tasks = [print_mission_progress_task]
    termination_task = asyncio.ensure_future(
        observe_is_in_air(drone, running_tasks))

    # Create a mission plan
    mission_items = []
    mission_items.append(MissionItem(47.398039859999997,
                                     8.5455725400000002,
                                     25,
                                     10,
                                     True,
                                     float('nan'),
                                     float('nan'),
                                     MissionItem.CameraAction.NONE,
                                     float('nan'),
                                     float('nan'),
                                     float('nan'),
                                     float('nan'),
                                     float('nan')))
    mission_items.append(MissionItem(47.398036222362471,
                                     8.5450146439425509,
                                     25,
                                     10,
                                     True,
                                     float('nan'),
                                     float('nan'),
                                     MissionItem.CameraAction.NONE,
                                     float('nan'),
                                     float('nan'),
                                     float('nan'),
                                     float('nan'),
                                     float('nan')))
    mission_items.append(MissionItem(47.397825620791885,
                                     8.5450092830163271,
                                     25,
                                     10,
                                     True,
                                     float('nan'),
                                     float('nan'),
                                     MissionItem.CameraAction.NONE,
                                     float('nan'),
                                     float('nan'),
                                     float('nan'),
                                     float('nan'),
                                     float('nan')))

    mission_plan = MissionPlan(mission_items)

    # Upload the mission plan to the drone
    await drone.mission.set_return_to_launch_after_mission(True)
    await drone.mission.upload_mission(mission_plan)

    # Arm the drone and start the mission
    await drone.action.arm()
    await drone.mission.start_mission()

    await termination_task

async def print_mission_progress(drone):
    async for mission_progress in drone.mission.mission_progress():
        print(f"Mission progress: "
            f"{mission_progress.current}/"
            f"{mission_progress.total}")
            
# async def observe_is_in_air(drone, running_tasks):
#     """Monitors whether the drone is flying or not and
#     terminates the mission when the drone landed.

#     Args:
#         drone: An instance of the drone object.
#         running_tasks: A list of running tasks (TBD)
#     """
#     print("-- observing in air")
#     previous_is_in_air = None
#     async for is_in_air in drone.telemetry.in_air():
#         if previous_is_in_air is False and is_in_air is True:
#             print("-- Mission started")
#             running_tasks.append(asyncio.ensure_future(print_mission_progress(drone)))

#         elif previous_is_in_air is True and is_in_air is False:
#             print("-- Mission finished")
#             running_tasks.pop(0).cancel()
#             return

#         previous_is_in_air = is_in_air

async def observe_is_in_air(drone, running_tasks):
    """ Monitors whether the drone is flying or not and
    returns after landing """

    was_in_air = False

    async for is_in_air in drone.telemetry.in_air():
        if is_in_air:
            was_in_air = is_in_air

        if was_in_air and not is_in_air:
            for task in running_tasks:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            await asyncio.get_event_loop().shutdown_asyncgens()

            return

if __name__ == "__main__":
    #loop = asyncio.get_event_loop()
    #loop.run_until_complete(run())
    #run the asyncio loop
    asyncio.run(run())
