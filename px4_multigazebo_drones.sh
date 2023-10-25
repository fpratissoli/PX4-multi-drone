#!/bin/bash

# Change directory to the location of the px4 executable
cd ~/PX4-Autopilot/build/px4_sitl_default/bin/

# Command 1
#PX4_SYS_AUTOSTART=4001 PX4_GZ_MODEL=x500 ./px4 -i 1 &
gnome-terminal --tab -- bash -c "PX4_SYS_AUTOSTART=4001 PX4_GZ_MODEL=x500 ./px4 -i 1; exec bash"

# Sleep for a moment to allow the first command to start
sleep 8

# Open a new terminal and execute Command 2
# PX4_SYS_AUTOSTART=4001 PX4_GZ_MODEL_POSE="0,1" PX4_GZ_MODEL=x500 ./px4 -i 2
gnome-terminal --tab -- bash -c "PX4_SYS_AUTOSTART=4001 PX4_GZ_MODEL_POSE=\"0,1\" PX4_GZ_MODEL=x500 ./px4 -i 2; exec bash"

