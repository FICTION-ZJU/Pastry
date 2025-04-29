#!/bin/bash

# Check if input file is provided
if [ "$#" -ne 1 ]; then
    echo "Usage: ./run.sh input.txt"
    exit 1
fi

# Get absolute path of input file
INPUT_FILE=$(realpath "$1")
INPUT_DIR=$(dirname "$INPUT_FILE")
FILENAME=$(basename "$INPUT_FILE")

# Run the Docker container with resolved paths
docker run --platform linux/amd64 --rm -v "$INPUT_DIR:/data" pastry:latest -c "cd pastry && poetry run python pastry.py --input "/data/$FILENAME""