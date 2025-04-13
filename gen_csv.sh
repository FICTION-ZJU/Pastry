#!/bin/bash 

echo "input,AST,PAST,time" > pastry.csv
find benchmarks -name "*.txt" -type f | sort | xargs -I{} poetry run python pastry.py --input {} --csv --timeout 1 | tee -a pastry.csv