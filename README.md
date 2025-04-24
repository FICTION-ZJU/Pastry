# Pastry: The Positive Almost-Sure Termination Prototype

![logo](img/pastry_probabilistic_termination_verification_toolpastry_letters.png)

Pastry is an academic prototype for deciding (positive) almost-sure termination ((P)AST) of essentially 1-dimensional probabilistic counter programs (PCPs).
For more technical details, please refer to our CAV'25 paper:

> Sergei Novozhilov, Mingqi Yang, Mingshuai Chen, Zhiyang Li, Jianwei Yin:
On the Almost-Sure Termination of Probabilistic Counter Programs. In Proc. of CAV 2025.

## Contents
- [Project Structure](#project-structure)
- [Requirements](#requirements)
- [Setup (Docker)](#setup-docker)
- [Smoke test (Docker)](#smoke-test-docker)
- [Setup (Poetry)](#setup-poetry)
- [Smoke test (Poetry)](#smoke-test-poetry)
- [Replicate the results from the paper](#replicate-the-results-from-the-paper)
- [Write your own example](#write-your-own-example)
- [Run your own example](#run-your-own-example)
- [Becnhmarks](#benchmarks)
- [Build Artifacts](#build-artifacts)
- [One-Click Table Generation](#one-click-table-generation)


## Requirements
- Install Docker (https://www.docker.com/get-started/) in case you do not have it yet.
- Experiments in the paper are conducted on a 3.22 GHz Apple M1 Pro processor with 16GB RAM running macOS Sonoma. Make sure to have similar specs when comparing timing results and consider differences running in a sandbox (docker).

## Project Structure

We provide two possilbe ways of project setup: 
1. Building a docker container 
2. Using [Poetry](https://python-poetry.org/) package manager

## Setup (Docker)
To create a docker container from the provided tar file:
```bash
docker build -t pastry:latest .
```

## Smoke test (Docker)

For a quick test to see if everything works:

```bash
docker run --rm pastry:latest pastry/batch_test.sh --input \
test/ast.txt \
test/past.txt \
test/none.txt
```

Expected output is: 
```
Running: test/ast.txt
AST  : True
PAST : False
Time : 0.097s
Running: test/past.txt
AST  : True
PAST : True
Time : 0.013s
Running: test/none.txt
AST  : False
PAST : False
Time : 0.01s
```

## Setup (Poetry)
```bash
poetry install
```

## Smoke test (Poetry)

To test the correctness of the setup, run:

```bash
cd poetry && poetry run python pastry.py --input \
./test/ast.txt \
./test/past.txt \
./test/none.txt
```

Expected output is: 
```
Running: ./test/ast.txt
AST  : True
PAST : False
Time : 0.053s
Running: ./test/past.txt
AST  : True
PAST : True
Time : 0.017s
Running: ./test/none.txt
AST  : False
PAST : False
Time : 0.011s
```

## Replicate the results from the paper

To run the benchmark suite, run: 

```bash
docker run --rm -v $(pwd)/outputs:/home/artifact/pastry/outputs -v $(pwd)/result:/home/artifact/result --entrypoint bash pastry:latest pastry/benchmark.sh
```

The detailed logs will be available in the `./outputs/logs` folder

## Writing your own example

This section describes the input language used by Pastry and explains how users can write and annotate their own probabilistic counter programs. Example programs are provided to illustrate the format.


### Syntax of PCPs


```
start: declarations instructions

declarations: declaration* -> declarations

declaration: "int" var "=" INT

instructions: instruction* -> instructions

instruction: "skip"                                 -> skip
            | "while" "(" guard ")" block           -> while
            | "if" "(" guard ")" block "else" block -> if
            | block "[" PROB "]" block              -> choice
            | var ":=" var "+" NAT                  -> inc_assign
            | var ":=" var "-" NAT                  -> dec_assign

block: "{" instruction* "}"

expression: var                                   -> var
            | INT                                 -> int
            | expression "+" expression           -> add
            | expression "-" expression           -> sub
            | expression "*" expression           -> mul
            | expression "**" NAT                 -> pow
            | "MOD" "(" expression "," POSINT ")" -> mod
            | "DIV" "(" expression "," POSINT ")" -> div

guard: "true"                                    -> true
        | "false"                                -> false
        | expression ">" expression              -> gt
        | expression "<" expression              -> lt
        | expression ">=" expression             -> ge
        | expression "<=" expression             -> le
        | "Eq" "(" expression "," expression ")" -> eq
        | "Ne" "(" expression "," expression ")" -> neq
        | "(" guard ")" "&" "(" guard ")"        -> and
        | "(" guard ")" "|" "(" guard ")"        -> or
        | "Not" "(" guard ")"                    -> not

literal: INT     -> int
        | NAT    -> nat         
        | POSINT -> pos_int      
        | PROB   -> prob         

var: CNAME
```


**Note:** Non-counting assignments like `var := c` are not allowed. Instead, use two consecutive counter-style loops to simulate it as
``` 
while (var < c) { var := var + 1 }
while (var > c) { var := var - 1 }
```

### Annotation rules
In addition to 1-d PCPs, Pastry admits four classes of $k$-d PCPs that are reducible to $1$-d PCPs while preserving their termination properties (see Section 5 of the paper). These four classes include (i) All But One Counters are Bounded; (ii) Monotone Counters; (iii) Conditionally Bounded Counters; and (iv) Constant Probability Programs. For Classes (ii) and (iv), Pastry supports automated checking of whether an input $k$-d PCP belongs to these categories and thus decides termination without any user hint. However, For Classes (i) and (iii), users need to provide correct annotations to assist the analysis：
- For *All But One Counters are Bounded PCPs*, users need to annotate the unbounded variable and the bounds (in the form of closed intervals) for the other variables at the top of the program using the following format:```/*@Bounded, <unbounded_var>, <var1>,[<lower>,<upper>], <var2>, [<lower>,<upper>], ...@*/```. If all variable are bounded, ```<unbounded_var>``` can be omitted from the annotation.
- For *Conditionally Bounded PCPs*, users need to provide valid constants (see Section 5 of the paper) at the top of the program using the following format: ```/*@CondBounded, y, x1[A1,B1,C1,D1], x2[A2,B2,C2,D2], ...@*/```

### Program examples

An example of $1$-d PCP:
```
# this is a comment
int x = 10
while(x**5 - 4*x**2 + x >= 0){
    if(x <= 1000){
        {x := x - 2}[1/2]{x := x + 1} 
    }else{
        {x := x - 1}[1/2]{x := x + 2} 
    }
}
```

An example of All But One Counters are Bounded PCP:
```
# this is a comment
/*@Bounded,i,[0,1],j,[0,2]@*/
int i = 0
int j = 0
while(i < 1){
    if(j < 2){
        i := i + 1
    }else{
        j := j - 2
    }
}
```

An example of Monotone PCP:
```
# this is a comment
int x = -3
int y = 0
while(x < 0){
    {x := x + 1}[1/10]{skip}
    while(y >= 1){
        {y := y - 1}[2/3]{y := y - 2}
    }
    y := y + 1
}
```

An example of Conditionally Bounded PCP:
```
# this is a comment
/*@CondBounded,y,x[1,1,0,1]@*/
int x = 1
int y = 1 
while(x + y >= 0){
    {x := x + 1; y := y + 1}[0.5]{x := x - 1; y := y - 1}
    if(Eq(x, y)){
        {y := y + 1}[0.5]{y := y - 1}
    }else{

    }
}
```

An example of Constant PCP:
```
# this is a comment
int T = 0
int H = 0
while(T - H > -1){
    {T := T + 1}[9/10]{H := H + 1}
}
```

More examples can be found in the benchmarks folder.

### Run your own example

Suppose you saved your example in a file named `xxx.txt` in the path /home/artifact/benchmarks/pastry. Then the tool can be run as:

```bash
./run.sh pastry xxx
```

### Run (with Poetry)
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

To run on the benchmark suite: 

```bash
find benchmarks -name "*.txt" -type f | sort | xargs -I{} poetry run python pastry.py --input {}
```

### Run (with Docker)
Docker image can be envoked either using a wrapper: 

```bash
bash run.sh program.txt
```

optionally, it can be done by mounting a directory containing the target intput. Suppose, the target program is located at `/host/location/program.txt`, then docker image can be invoked as 

```bash 
docker run --rm -v /host/location/:/data pastry:latest --input /data/program.txt
```



### Benchmarks

To run on the benchmark suite, run: 

```bash
docker run --rm -v $(pwd)/outputs:/app/outputs --entrypoint bash pastry:latest benchmark.sh 
```

------

### Build Artifacts 

To build a docker image, run: 

```bash
docker build -t pastry:latest .
```


To run the docker image on a file located at the host's path `/path/to/data/input.txt`, run

```bash
docker run --rm -v /path/to/data:/data pastry:latest --input /data/input.txt
```


### One Click Table Generation
To generate csv file for pastry:

```bash
bash gen_csv.sh
```
