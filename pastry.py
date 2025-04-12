import sys, os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


from src.configs.logging_config import setup_logger
from pastry_core import run_core_analysis
from argparse import ArgumentParser
import time
import glob
import logging



parser = ArgumentParser(description="Run Pastry on probabilistic counter programs stored in files")

parser.add_argument(
    "--input",
    dest="input",
    required=True,
    type=str,
    nargs="+",
    help="A list of files to run Pastry on"
)

parser.add_argument(
    "--timeout",
    dest="timeout",
    type=int,
    default=90,
    help="Timeout in seconds for each benchmark (default: 90)"
)

def main():
    setup_logger(logging.CRITICAL, logging.DEBUG)

    args = parser.parse_args()
    args.input = [b for bs in map(glob.glob, args.input) for b in bs]

    for path in args.input:
        print(f"Running: {path}")
        with open(path, "r", encoding="utf-8") as f:
            prog_str = f.read()

        start = time.time()
        result = run_core_analysis(prog_str)
        end = time.time()

        print(f"AST  : {result['ast']}")
        print(f"PAST : {result['past']}")
        print(f"Time : {round(end - start, 3)}s")

if __name__ == "__main__":
    main()