# Drones and PX4
## Initial SetUP

**Download the PX4 repo**
```
cd /path/to/workspace

git clone https://github.com/PX4/PX4-Autopilot.git --recursive
```
**Install the software**
```
cd /path/to/workspace

bash ./PX4-Autopilot/Tools/setup/ubuntu.sh
```
**Download and Install QGroundControl software in your workspace**

[https://docs.qgroundcontrol.com/master/en/qgc-user-guide/getting_started/download_and_install.html](https://)

**Install the repository requirements**
```
cd DRONES-PX4

pip install -r requirements.txt
```
## How to Run a Simple Simulation
### Choose a simulator among the following choices (jmavsim / gazebo garden / gazebo classic / custom):

**Jmavsim Simulator** \
Start JMavSim with iris (default vehicle model):
`make px4_sitl jmavsim`

**Gazebo Simulator (Ubuntu22 - gazebo ignition/gazebo garden)** \
Start Gazebo with the x500 multicopter:
`make px4_sitl gz_x500`

Gazebo classic has more models and worlds that gazebo ignition, **_IF you want_** to install gazebo classic on ubuntu22, remove gazebo garden and reinstall gazebo classic 11 (RISK of dependancies issues!):
```
sudo apt remove gz-garden
sudo apt install aptitude
sudo aptitude install gazebo libgazebo11 libgazebo-dev
```

**Gazebo Simulator (Ubuntu20 - gazebo classic)** \
Start Gazebo with the iris multicopter:
`make px4_sitl_default gazebo-classic`

**_IF you want_** to use gazebo garden in ubuntu20 (the procedure will uninstall gazebo-classic!):
```
sudo wget https://packages.osrfoundation.org/gazebo.gpg -O /usr/share/keyrings/pkgs-osrf-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/pkgs-osrf-archive-keyring.gpg] http://packages.osrfoundation.org/gazebo/ubuntu-stable $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/gazebo-stable.list > /dev/null
sudo apt-get update
sudo apt-get install gz-garden
```

**Custom Simulator** \
Start PX4 with no simulator (i.e. to use your own "custom" simulator):
`make px4_sitl none_iris`

### Then you che start the connection with the ground control and the mavsdk api

**Start the QGroundControl App:**
`./QGroundControl.AppImage`

**Write your code in *drone_control.py* main function and run the file:**
`python3 drone_control.py`

### Set custom default Takeoff Location:
**Jmavsim/Gazebo-Classic Simulator**:
```
export PX4_HOME_LAT=44.69865720233633
export PX4_HOME_LON=10.645858339984548
export PX4_HOME_ALT=30
make px4_sitl jmavsim
```
**Gazebo Garden**:
```
issue still open
```

## How to run a Multi-Vehicle Simulation



