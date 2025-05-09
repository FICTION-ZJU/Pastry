import sys, os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


from src.configs.logging_config import setup_logger
from pastry_core import run_core_analysis
from argparse import ArgumentParser
import time
import glob
import logging
import signal


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
    type=float,
    default=90.0,
    help="Timeout in seconds for each benchmark (default: 90)"
)

parser.add_argument(
    "--csv",
    dest="csv",
    action="store_true",
    help="Print results without header"
)


def main():
    args = parser.parse_args()
    args.input = [b for bs in map(glob.glob, args.input) for b in bs]
    
    for path in args.input:
        if not args.csv:
            print(f"Running: {path}")

        with open(path, "r", encoding="utf-8") as f:
            prog_str = f.read()

        # Extract file name without path and extension
        file_name = os.path.splitext(os.path.basename(path))[0]

        # Create a new logger for each input file
        setup_logger(file_name, logging.CRITICAL, logging.DEBUG)
        logger = logging.getLogger("pastry")


        # for handling timeouts
        def timeout_handler(signum, frame):
            raise TimeoutError("Function execution timed out")

        start = time.time()
        
        timeout_occured = False
        timeout = int(args.timeout)
        # Set the signal handler and a timeout
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout)

        try:
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(timeout)
            result = run_core_analysis(prog_str)
        except TimeoutError as e:
            timeout_occured = True
            result = {
                "ast": "TIMEOUT",
                "past": "TIMEOUT"
            }

        end = time.time()


        if not args.csv:
            if timeout_occured:
                print(f"AST  : None")
                print(f"PAST : None")
                print(f"Time : TO")
            else:
                print(f"AST  : {result['ast']}")
                print(f"PAST : {result['past']}")
                print(f"Time : {round(end - start, 3)}s")
        else:
            file_name_no_ext = os.path.splitext(os.path.basename(path))[0]
            if timeout_occured:
                print(f"{file_name_no_ext},None,None,TO")
            else:
                print(f"{file_name_no_ext},{result['ast']},{result['past']},{round(end - start, 3)}")
        

if __name__ == "__main__":
    main()
