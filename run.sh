#!/bin/bash

USAGE()
{
  echo "Usage: run.sh --run-all [--timeout | -t TIMEOUT]"
  echo "   or: run.sh <pastry | koat1 | koat2 | amber> <benchmark name> [--timeout | -t TIMEOUT]"
  echo ""
  echo "options:"
  echo "  <benchmark name>     The name of a benchmark without file suffix"
  echo "  --timeout, -t        Set timeout value in seconds (integer). The default value is 100"
  exit 2
}

cd "$(dirname "${BASH_SOURCE[0]}")"
arg_count=$#
if [ $arg_count -eq 0 ]; then
    USAGE
fi

if [ $arg_count -eq 1 ] || [ $arg_count -eq 3 ]; then
    if [ "$1" == "--run-all" ]; then
        if [ $arg_count -eq 1 ]; then
            mkdir -p result
            python3 run.py --run-all #> result/all_experimant_data.csv
        elif [ $2 != "-t" ] && [ $2 != "--timeout" ]; then
            USAGE
        elif [[ "$3" =~ ^[1-9][0-9]*$ ]]; then
            mkdir -p result
            python3 run.py --run-all $3 #> result/all_experimant_data.csv
        else
            USAGE
        fi
    else
        USAGE
    fi
elif [ "$1" == "pastry" ] || [ "$1" == "koat1" ] || [ "$1" == "koat2" ] || [ "$1" == "amber" ]; then
    if [ $arg_count -eq 2 ]; then
        python3 run.py $1 $2
    elif [ $arg_count -eq 4 ]; then
        if [ $3 != "-t" ] && [ $3 != "--timeout" ]; then
            USAGE
        fi
        if [[ "$4" =~ ^[1-9][0-9]*$ ]]; then
            python3 run.py $1 $2 $4
        else
            USAGE
        fi
    fi
else
  USAGE
fi