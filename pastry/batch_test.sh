#!/bin/bash

cd "$(dirname "${BASH_SOURCE[0]}")"
poetry run python3 ./pastry.py $*