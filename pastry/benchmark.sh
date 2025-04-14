#!/bin/bash

cd "$(dirname "${BASH_SOURCE[0]}")"
find -L benchmarks -name "*.txt" -type f | sort | xargs -I{} poetry run python pastry.py --input {}