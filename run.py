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
    # namelist = [file.name[:-4] for file in sorted(list(Path("./benchmarks/pastry").rglob("**/*.txt")), key = str)]
    namelist = [
        "symmetric_rw1", "symmetric_rw2", "biased_rw1", "biased_rw2", "biased_rw3", "biased_rw4",
        "binomial1", "binomial2", "geometric", "2d_bounded_rw", "geometric_gauss", "asymmetric_rw1",
        "complex_roots", "high_multiplicity", "neg_binomial", "nast_prog", "npast_prog", "dir_term",
        "irr_runtime", "tortoise_hare_un", "tortoise_hare", "tortoise_hare_dt", "generalized_rw",
        "two_endpoints", "infinite_loop", "two_loops", "ast_loop", "ast_rw", "biased_rw5", "skewed_rw",
        "asymmetric_rw2", "1d_poly_rw", "catmouse", "speedpldi4", "insertsort", "speedpldi2",
        "speedpldi3", "counterex1b", "Knuth-Yao_dice", "brp_protocol", "zeroconf"
    ]
    with open("result/all_experiment_data.csv", "w") as f:
        with Progress(
            TimeElapsedColumn(),
            BarColumn(),
            TextColumn("{task.percentage:.1f}%"),
            TextColumn("[bold blue]{task.description}")
        ) as progress:
            console = Console(file=f)
            task = progress.add_task("Running...", total = len(namelist))
            console.print("benchmark_name,Pastry,Amber,KoAT1,KoAT2")
            for name in namelist:
                progress.update(task, description = f"Running {name}")
                console.print(f"{name},{run_pastry(name, timeout, single = False)},{run_amber(name, timeout, single = False)},{run_koat1(name, timeout, single = False)},{run_koat2(name, timeout, single = False)}")
                progress.update(task, advance = 1)
            progress.update(task, description = "done.")

def run_pastry(benchmark_name, timeout = 100, single = True):
    p = Path("./benchmarks/pastry/")
    path = ""
    for file in p.glob(f"**/{benchmark_name}.txt"):
        path = str(file)
    if path == "":
        if single:
            print(f"No such benchmark named {benchmark_name}")
            exit(-1)
        else:
            return "-"
    result = subprocess.run(
        ["timeout", f"{timeout}s", "pastry/run.sh", f"./benchmarks/{path[18:]}", f"{2*timeout+100}"], 
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
        if line.startswith('PAST'):
            if line.split(':', 1)[1].strip() == "True":
                if single:
                    print("PAST : True")
                    print("AST  : True")
                det = True
        elif line.startswith('AST'):
            if line.split(':', 1)[1].strip() == "True":
                if single and not det:
                    print("PAST : False")
                    print("AST  : True")
            else:
                if single:
                    print("PAST : False")
                    print("AST  : False")
            det = True
        elif line.startswith('Time'):
            time = parse_time_to_seconds(line.split(":", 1)[1].strip())
    if det:
        if time != -1:
            if single:
                print(f"TIME : {time:.3f}s")
            else:
                return round(time, 3)
        else:
            sys.stderr.write(f"Cannot get running time of {benchmark_name} from pastry!")
            exit(-1)
    else:
        if single:
            print("pastry cannot determine termination property")
        else:
            return "-"

def run_koat1(benchmark_name, timeout = 100, single = True):
    # print(f"./benchmarks/KoAT1/{benchmark_name+".koat"}")
    if not Path(f"./benchmarks/KoAT1/{benchmark_name+".koat"}").exists():
        if single:
            print(f"No such benchmark named {benchmark_name}")
            exit(-1)
        else:
            return "-"
    result = subprocess.run(
        ["timeout", f"{timeout}s", "./baselines/KoAT1/main/run.sh", "-i", f"../benchmarks/{benchmark_name+".koat"}", "-t", f"{2*timeout+100}"], 
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
        if line.startswith('UPPER BOUND'):
            if single:
                print("PAST : True")
                print("AST  : True")
            det = True
        elif line.startswith('WARNING: The given program is not AST'):
            if single:
                print("PAST : False")
                print("AST  : False")
            det = True
        elif line.startswith('WARNING: The given program is AST, but not PAST'):
            if single:
                print("PAST : False")
                print("AST  : True")
            det = True
        elif line.startswith('TIME:'):
            time = float(line.split(":", 1)[1].strip())
    if det:
        if time != -1:
            if single:
                print(f"TIME : {time:.3f}s")
            else:
                return round(time, 3)
        else:
            sys.stderr.write(f"Cannot get running time of {benchmark_name} from KoAT1!")
            exit(-1)
    else:
        if single:
            print("KoAT1 cannot determine termination property")
        else:
            return "-"

def run_koat2(benchmark_name, timeout = 100, single = True):
    # print(f"./benchmarks/KoAT2/{benchmark_name+".koat"}")
    if not Path(f"./benchmarks/KoAT2/{benchmark_name+".koat"}").exists():
        if single:
            print(f"No such benchmark named {benchmark_name}")
            exit(-1)
        else:
            return "-"
    command = f'time ./koat2 analyse -i ./benchmarks/KoAT2/{benchmark_name+".koat"}'
    result = subprocess.run(
        ["timeout", f"{timeout}s", "bash", "-c", command], 
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
        if line.startswith('MAYBE'):
            det = False
            break
        elif line.startswith('WORST_CASE'):
            if single:
                print("PAST : True")
                print("AST  : True")
            det = True
    for line in result.stderr.splitlines():
        line = line.strip()
        if line.startswith("real"):
            time = float(line.split("real", 1)[1].strip())
    if det:
        if time != -1:
            if single:
                print(f"TIME : {time:.3f}s")
            else:
                return round(time, 3)
        else:
            sys.stderr.write(f"Cannot get running time of {benchmark_name} from KoAT2!")
            exit(-1)
    else:
        if single:
            print("KoAT2 cannot determine termination property")
        else:
            return "-"

def run_amber(benchmark_name, timeout = 100, single = True):
    # print(f"./benchmarks/amber/{benchmark_name}")
    if not Path(f"./benchmarks/amber/{benchmark_name}").exists():
        if single:
            print(f"No such benchmark named {benchmark_name}")
            exit(-1)
        else:
            return "-"
    result = subprocess.run(
        ["timeout", f"{timeout}s", "./baselines/amber/amber", f"./benchmarks/{benchmark_name}"], 
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
    error = False
    for line in result.stdout.splitlines():
        line = line.strip()
        if line.startswith('Something went wrong'):
            det = False
            error = True
            break
        elif line.startswith('PAST'):
            if line.split(':', 1)[1].strip() == "Yes":
                if single:
                    print("PAST : True")
                    print("AST  : True")
                det = True
        elif line.startswith('AST'):
            if line.split(':', 1)[1].strip() == "Yes":
                if single and not det:
                    print("PAST : False")
                    print("AST  : True")
            else:
                if single:
                    print("PAST : False")
                    print("AST  : False")
            det = True
        elif line.startswith('Computation time:'):
            time = parse_time_to_seconds(line.split(":", 1)[1].strip())
    if det:
        if time != -1:
            if single:
                print(f"TIME : {time:.3f}s")
            else:
                return round(time, 3)
        else:
            sys.stderr.write(f"Cannot get running time of {benchmark_name} from amber!")
            exit(-1)
    else:
        if single:
            if error:
                print('An error occurred:')
                print('stdout:')
                print(result.stdout)
                print('stderr:')
                print(result.stderr)
                exit(-1)
            else:
                print("amber cannot determine termination property")
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

    elif first_arg == "pastry":
        if len(sys.argv) == 3:
            run_pastry(sys.argv[2])
        else:
            run_pastry(sys.argv[2], int(sys.argv[3]))

    elif first_arg == "koat1":
        if len(sys.argv) == 3:
            run_koat1(sys.argv[2])
        else:
            run_koat1(sys.argv[2], int(sys.argv[3]))

    elif first_arg == "koat2":
        if len(sys.argv) == 3:
            run_koat2(sys.argv[2])
        else:
            run_koat2(sys.argv[2], int(sys.argv[3]))

    elif first_arg == "amber":
        if len(sys.argv) == 3:
            run_amber(sys.argv[2])
        else:
            run_amber(sys.argv[2], int(sys.argv[3]))

    else:
        print("Unknown command:", first_arg)

if __name__ == "__main__":
    main()
