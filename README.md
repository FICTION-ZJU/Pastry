### Getting Started

```bash
poetry install
```


### Running 
Pastry accepts a list of program files, printing the termination status for each of the file, for example

```bash
poetry run python pastry.py --input \
benchmarks/src01/2d_bounded_rw.txt \
benchmarks/src01/biased_rw1.txt
```

The expected output (time measurments will vary from system to system): 

```
Running: benchmarks/src01/2d_bounded_rw.txt
AST  : True
PAST : True
Time : 1.58s
Running: benchmarks/src01/biased_rw1.txt
AST  : False
PAST : False
Time : 0.02s
```

To run on the benchmar suite: 

```bash
find benchmarks -name "*.txt" -type f | sort | xargs -I{} poetry run python pastry.py --input {}
```


### Building Artifacts 

To build a docker image, run: 

```bash
docker build -t pastry:latest .
```


To run the docker image on a file located at the host's path `/path/to/data/input.txt`, run

```bash
docker run --rm -v /path/to/data:/data pastry:latest --input /data/input.txt
```

### Benchmarks

To run on the benchmark suite, run: 

```bash
docker run --rm -v $(pwd)/outputs:/app/outputs pastry:latest --input /app/benchmarks/src01/2d_bounded_rw.txt
```

