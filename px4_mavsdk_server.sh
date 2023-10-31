#!/bin/bash

# Check for the required arguments
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 grpc_port udp_port"
    exit 1
fi

# Assign the command line arguments to variables
grpc_port="$1"
udp_port="$2"

# Read the mavsdk_server path from the JSON configuration file
config_file="config.json"

# Check if the configuration file exists
if [ -f "$config_file" ]; then
    MavSdkServerPath=$(jq -r '.MavSdkServerPath' "$config_file")

    if [ -z "$MavSdkServerPath" ]; then
        echo "MavSdkServerPath is not defined in the configuration file."
        exit 1
    fi
else
    echo "Configuration file not found: $config_file"
    exit 1
fi

# Replace ~ with $HOME in the path
MavSdkServerPath="${MavSdkServerPath/\~/$HOME}"
#echo "My folder is located at: $MavSdkServerPath"

# Construct and run the mavsdk_server command
"$MavSdkServerPath" -p "$grpc_port" "udp://:$udp_port"
