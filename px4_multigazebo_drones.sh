#!/bin/bash

# Read the mavsdk_server path from the JSON configuration file
config_file="config.json"

# Check if the configuration file exists
if [ -f "$config_file" ]; then
    PX4_gazebo_path=$(jq -r '.PX4_gazebo_path' "$config_file")
    GRPC_PORT_BASE=$(jq -r '.GRPC_PORT_BASE' "$config_file")
    UDP_PORT_BASE=$(jq -r '.UDP_PORT_BASE' "$config_file")
    NUM_DRONES=$(jq -r '.NUM_DRONES' "$config_file")

    if [ -z "$PX4_gazebo_path" ]; then
        echo "PX4_gazebo_path is not defined in the configuration file."
        exit 1
    fi

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

# Replace ~ with $HOME in the path
# Path to PX4 Gazebo (ensure this is correctly set in your environment)
PX4_gazebo_path="${PX4_gazebo_path/\~/$HOME}"

# Start the Gazebo Simulator
#gnome-terminal --tab -- bash -c "python3 simulation-gazebo"
#sleep 3

# Distance between agents (in meters)
AGENT_DISTANCE=5  # Change this to adjust the spacing between agents

# Function to generate position randomly
# generate_position() {
#     x=$((RANDOM % 10))
#     y=$((RANDOM % 10))
#     z=$((RANDOM % 10))
#     echo "$x $y $z"
# }

# Function to generate position based on index and distance
generate_position() {
    local index=$1
    local distance=$2
    local x=$(( (index % 3) * distance ))  # Arrange in a 3xN grid
    local y=$(( (index / 3) * distance ))
    echo "$x,$y"
}

# Launch agents
for i in $(seq 1 $NUM_DRONES)
do
    position=$(generate_position $((i-1)) $AGENT_DISTANCE)
    cmd="HEADLESS=1 PX4_SYS_AUTOSTART=4001 PX4_GZ_MODEL_POSE=\"$position\" PX4_GZ_MODEL=x500 $PX4_gazebo_path -i $i; exec bash"
    
    echo "Launching agent $i at position $position"
    gnome-terminal --tab -- bash -c "$cmd"
    
    # Sleep to allow each process to start (adjust if needed)
    sleep 8
done

echo "Launched $NUM_DRONES PX4 instances."

# Create a for loop to iterate from 0 to num_agents
for ((i = 1; i <= NUM_DRONES; i++)); do
  # Start each process in the background
  echo "Started mavsdk_server for drone $i at GRPC port $((GRPC_PORT_BASE+i)) and UDP port $((UDP_PORT_BASE+i))"
  (./px4_mavsdk_server.sh $((GRPC_PORT_BASE+i)) $((UDP_PORT_BASE+i))) &
done

# Wait for all background processes to complete
wait