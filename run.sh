#!/bin/bash

USAGE()
{
    echo "Usage: run.sh --run-all [--timeout | -t TIMEOUT]"
    echo "   or: run.sh --single <benchmark name> [--timeout | -t TIMEOUT]"
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
            python3 run.py --run-all
        elif [ $2 != "-t" ] && [ $2 != "--timeout" ]; then
            USAGE
        elif [[ "$3" =~ ^[1-9][0-9]*$ ]]; then
            mkdir -p result
            python3 run.py --run-all $3
        else
            USAGE
        fi
    else
        USAGE
    fi
elif [ $arg_count -eq 2 ] || [ $arg_count -eq 4 ]; then
    if [ "$1" == "--single" ]; then
        if [ $arg_count -eq 2 ]; then
            python3 run.py --single $2
        elif [ $2 != "-t" ] && [ $2 != "--timeout" ]; then
            USAGE
        elif [[ "$3" =~ ^[1-9][0-9]*$ ]]; then
            mkdir -p result
            python3 run.py --single $2 $3
        else
            USAGE
        fi
    else
        USAGE
    fi
else
    USAGE
fi