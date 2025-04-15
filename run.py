import sys
import subprocess
import re
from pathlib import Path
from rich.progress import Progress, TextColumn, BarColumn, TimeElapsedColumn
from rich.console import Console

def parse_time_to_seconds(time_str):
    pattern = r'(?:(\d+(?:\.\d+)?)h)?\s*(?:(\d+(?:\.\d+)?)m)?\s*(?:(\d+(?:\.\d+)?)s)?'
    match = re.fullmatch(pattern, time_str.strip())
    if not match:
        raise ValueError("Invalid time format")

    h, m, s = match.groups()
    total_seconds = (
        (float(h) * 3600 if h else 0) +
        (float(m) * 60 if m else 0) +
        (float(s) if s else 0)
    )
    return total_seconds


def run_all(timeout = 100):
    namelist = [
        "symmetric_rw1", "symmetric_rw2", "biased_rw1", "biased_rw2", "biased_rw3", "biased_rw4",
        "binomial1", "binomial2", "geometric", "2d_bounded_rw", "geometric_gauss", "asymmetric_rw1",
        "complex_roots", "high_multiplicity", "neg_binomial", "nast_prog", "npast_prog", "dir_term",
        "irr_runtime", "tortoise_hare_un", "tortoise_hare", "tortoise_hare_dt", "generalized_rw",
        "two_endpoints", "infinite_loop", "two_loops", "ast_loop", "ast_rw", "biased_rw5", "skewed_rw",
        "asymmetric_rw2", "1d_poly_rw", "catmouse", "speedpldi4", "insertsort", "speedpldi2",
        "speedpldi3", "counterex1b", "Knuth-Yao_dice", "brp_protocol", "zeroconf"
    ]
    with open("result/absynth_all_experiment_data.csv", "w") as f:
        with Progress(
            TimeElapsedColumn(),
            BarColumn(),
            TextColumn("{task.percentage:.1f}%"),
            TextColumn("[bold blue]{task.description}")
        ) as progress:
            console = Console(file=f)
            task = progress.add_task("Running...", total = len(namelist))
            console.print("benchmark_name,Absynth")
            for name in namelist:
                progress.update(task, description = f"Running {name}")
                console.print(f"{name},{run_absynth(name, timeout, single = False)}")
                progress.update(task, advance = 1)
            progress.update(task, description = "done.")

def run_absynth(benchmark_name, timeout = 100, single = True):
    p = Path("./benchmarks/")
    path = ""
    for file in p.glob(f"**/{benchmark_name}.imp"):
        path = str(file)
    if path == "":
        if single:
            print(f"No such benchmark named {benchmark_name}")
            exit(-1)
        else:
            return "-"
    result = subprocess.run(
        ["gtimeout", f"{timeout}s", "absynth/absynth", "-degree", "2", "-dump-stats", f"benchmarks/{benchmark_name}.imp"], 
        capture_output=True,
        text=True
    )
    if result.returncode == 124:
        if single:
            print('TIMEOUT')
            exit(0)
        else:
            return "TO"
    elif result.returncode != 0:
        if result.returncode != 1 or "Sorry, I could not find a bound" not in result.stdout:
            if single:
                print('An error occurred:')
                print(f"return code: {result.returncode}")
                print('stdout:')
                print(result.stdout)
                print('stderr:')
                print(result.stderr)
                exit(-1)
            else:
                return "-"
    time = -1
    det = False
    for line in result.stdout.splitlines():
        line = line.strip()
        if line.startswith('Sorry, I could not find a bound'):
            det = False
            break
        elif line.startswith('Water mark bound'):
            if single:
                print("PAST : True")
                print("AST  : True")
            det = True
        elif "Total runtime" in line:
            time = parse_time_to_seconds(line.split(":", 1)[1].strip())
    if det:
        if time != -1:
            if single:
                print(f"TIME : {time:.3f}s")
            else:
                return round(time, 3)
        else:
            sys.stderr.write(f"Cannot get running time of {benchmark_name} from absynth!")
            exit(-1)
    else:
        if single:
            print("absynth cannot determine termination property")
        else:
            return "-"

def main():
    if len(sys.argv) < 2:
        print("No arguments provided.")
        return

    first_arg = sys.argv[1]

    if first_arg == "--run-all":
        if len(sys.argv) == 3:
            run_all(int(sys.argv[2]))
        else:
            run_all()

    elif first_arg == "--single":
        if len(sys.argv) == 3:
            run_absynth(sys.argv[2])
        else:
            run_absynth(sys.argv[2], int(sys.argv[3]))

    else:
        print("Unknown command:", first_arg)

if __name__ == "__main__":
    main()
