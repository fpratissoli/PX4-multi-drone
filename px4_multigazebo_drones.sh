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

#Start the mavsdk_servers for each drone
# Change directory to the current location
cd $(pwd)

sleep 3

# Read the mavsdk_server path from the JSON configuration file
config_file="config.json"

# Check if the configuration file exists
if [ -f "$config_file" ]; then
    GRPC_PORT_BASE=$(jq -r '.GRPC_PORT_BASE' "$config_file")
    UDP_PORT_BASE=$(jq -r '.UDP_PORT_BASE' "$config_file")
    NUM_DRONES=$(jq -r '.NUM_DRONES' "$config_file")

    if [ -z "$GRPC_PORT_BASE" ]; then
        echo "GRPC_PORT_BASE is not defined in the configuration file."
        exit 1
    fi

    if [ -z "$UDP_PORT_BASE" ]; then
        echo "UDP_PORT_BASE is not defined in the configuration file."
        exit 1
    fi

    if [ -z "$NUM_DRONES" ]; then
        echo "NUM_DRONES is not defined in the configuration file."
        exit 1
    fi

else
    echo "Configuration file not found: $config_file"
    exit 1
fi

# Create a for loop to iterate from 0 to num_agents
for ((i = 0; i < NUM_DRONES; i++)); do
  # Start each process in the background
  echo "Started mavsdk_server for drone $i at GRPC port $((GRPC_PORT_BASE+i)) and UDP port $((UDP_PORT_BASE+i))"
  (./px4_mavsdk_server.sh $((GRPC_PORT_BASE+i)) $((UDP_PORT_BASE+i))) &
done

# Wait for all background processes to complete
wait