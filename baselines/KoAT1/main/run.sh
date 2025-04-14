#!/bin/bash

TIMEOUT=300

usage()
{
  echo "Usage: run.sh [ -i | --input FILE ] [ -t | --timeout TIMEOUT ]"
  exit 2
}

PARSED_ARGUMENTS=$(getopt -a -n run.sh -o t:i:r:h: --long html,input:,result:,timeout:, -- "$@")
VALID_ARGUMENTS=$?
if [ "$VALID_ARGUMENTS" != "0" ]; then
  usage
fi

HTML=""

eval set -- "$PARSED_ARGUMENTS"
while :
do
  case "$1" in
    -i | --input)   INPUT="$2" ; shift 2 ;;
    -t | --timeout) TIMEOUT="$2" ; shift 2 ;;
    # -- means the end of the arguments; drop this, and break out of the while loop
    --) shift; break ;;
    # If invalid options were passed, then getopt should have reported an error,
    # which we checked as VALID_ARGUMENTS when getopt was called...
    *) echo "Unexpected option: $1 - this should not happen."
       usage ;;
  esac
done

cd "$(dirname "${BASH_SOURCE[0]}")"
./koat2 analyse -i ${INPUT};


