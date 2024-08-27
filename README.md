# Drones and PX4
## Initial SetUP

**Download the PX4 repo**

`cd /path/to/workspace`

`git clone https://github.com/PX4/PX4-Autopilot.git --recursive`

**Install the software**

`cd /path/to/workspace`

`bash ./PX4-Autopilot/Tools/setup/ubuntu.sh`

**Download and Install QGroundControl software in your workspace**

[https://docs.qgroundcontrol.com/master/en/qgc-user-guide/getting_started/download_and_install.html](https://)

**Install the repository requirements**

`cd DRONES-PX4`

`pip install -r requirements.txt`

## How to Run a Simulation

**Jmavsim Simulator** \
Start JMavSim with iris (default vehicle model):

`make px4_sitl jmavsim`

**Gazebo Simulator (Ubuntu22)** \
Start Gazebo with the x500 multicopter:

`make px4_sitl gz_x500`

**Custom Simulator** \
Start PX4 with no simulator (i.e. to use your own "custom" simulator):

`make px4_sitl none_iris`

**Start the QGroundControl App**

**Run the drone_control.py code**

`python3 drone_control.py`




