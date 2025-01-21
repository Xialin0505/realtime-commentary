#!/bin/bash

# Store the first argument in a variable
action=$1

if [ "$action" == "up" ]; then
    docker-compose up

elif [ "$action" == "down" ]; then
    docker-compose down
    docker-compose down --volumes

else
    echo "Invalid argument: $action"
    echo "Usage: $0 up|down"
    exit 1

fi