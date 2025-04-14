



# Pastry: the Positive AST pRototYpe

![logo](pastry/img/pastry_probabilistic_termination_verification_toolpastry_letters.png)

Pastry is an academic prototype for deciding (positive) Almost-Sure Termination of essentially 1-d probabilistic counter programs (PCPs).

## Contents
- [Project Structure](#project-structure)
- [Requirements](#requirements)
- [Setup (Docker)](#setup-docker)
- [Smoke test (Docker)](#smoke-test-docker)
- [Setup (Poetry)](#setup-poetry)
- [Smoke test (Poetry)](#smoke-test-poetry)
- [Replicating the results from the paper](#replicating-the-results-from-the-paper)
- [Writing your own example](#writing-your-own-example)
- [Running your own example](#running-your-own-example)
- [Becnhmarks](#benchmarks)
- [Building Artifacts](#building-artifacts)
- [One-Click Table Generation](#one-click-table-generation)


## Requirements
- Install Docker (https://www.docker.com/get-started/) in case you do not have it yet.
- Experiments in the paper are conducted on a 3.22 GHz Apple M1 Pro processor with 16GB RAM running macOS Sonoma. Make sure to have similar specs when comparing timing results and consider differences running in a sanbox (docker).

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
docker run --rm -v $(pwd):/data pastry:latest --input \
/data/test/ast.txt \
/data/test/past.txt \
/data/test/none.txt
```

Expected output is: 
```
Running: /data/test/ast.txt
AST  : True
PAST : False
Time : 0.097s
Running: /data/test/past.txt
AST  : True
PAST : True
Time : 0.013s
Running: /data/test/none.txt
AST  : False
PAST : False
Time : 0.01s
```

## Setup (Poetry)
```bash
poetry install
```

## Smoke test (Poetry)

To thest the correctness of the setup, run:

```bash
poetry run python pastry.py --input \
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

## Replicating the results from the paper

To run the benchmark suite, run: 

```bash
docker run --rm -v $(pwd)/outputs:/app/outputs --entrypoint bash pastry:latest benchmark.sh 
```

The detailed logs will be available in the `./outputs/logs/` folder

## Writing your own example

This section describes the input language used by Pastry and how users can write, annotate their own probabilistic counter programs, along with example programs illustrating the format.


### Progeam syntax rules:


```
start: declarations instructions

declarations: declaration* -> declarations

declaration: "int" var "=" INT

instructions: instruction* -> instructions

instruction: "skip"                                                 -> skip
            | "while" "(" guard ")" "{" block "}"                   -> while
            | "if" "(" guard ")" "{" block "}" "else" "{" block "}" -> if
            | "{" block "}" "[" PROB "]" "{" block "}"              -> choice
            | var ":=" var "+" NAT                                  -> inc_assign
            | var ":=" var "-" NAT                                  -> dec_assign

block: "{" instruction* "}"

expression: var                                  -> var
           | INT                                 -> nat
           | expression "+" expression           -> add
           | expression "-" expression           -> sub
           | expression "*" expression           -> mul
           | expression "**" NAT                 -> pow
           | "MOD" "(" expression "," POSINT ")" -> mod
           | "DIV" "(" expression "," POSINT ")" -> div

guard: "true"                                  -> true
      | "false"                                -> false
      | expression ">" expression              -> gt
      | expression "<" expression              -> lt
      | expression ">=" expression             -> ge
      | expression "<=" expression             -> le
      | "Eq" "(" expression "," expression ")" -> eq
      | guard "&" guard                        -> and
      | guard "|" guard                        -> or
      | "Not" "(" guard ")"                    -> not

literal: INT     -> int
        | NAT    -> nat         
        | POSINT -> pos_int      
        | PROB   -> prob         

var: CNAME
```




**Note:** Direct assignment format like `var := c` are not allowed. Instead, use two consecutive counter-style loops to simulate the direct assignment:
 ``` 
 while (var < c) { var := var + 1 }
 while (var > c) { var := var - 1 }
 ```

### Annotation rules
In addition to 1-d PCPs, Pastry also supports verification for four classes of k-d PCPs: Monotone PCPs, Constant PCPs, All But One Counters are Bounded PCPs, and Conditionally Bounded PCPs. For Monotone PCPs and Constant PCPs, Pastry supports automated checking of whether an input k-d PCP belongs to these categories and thus perform verification without any user intervention. However, For **All But One Counters are Bounded PCPs** and **Conditionally Bounded PCPs**, users are required to provide correct annotations to assist the analysis：
- For **All But One Counters are Bounded PCPs**, users are required to annotate the unbounded variable and the closed intervals for other variables at the top of the program using the following format: ```/*@Bounded, <unbounded_var>, <var1>[<lower>,<upper>], <var2>[<lower>,<upper>], ...@*/```. If all variable are bounded, the ```<unbounded_var>``` can be omitted from the annotation: ```/*@Bounded, <var1>[<lower>,<upper>], <var2>[<lower>,<upper>], ...@*/```
- For **Conditionally Bounded PCPs**, users are required to provide coefficient information at the top of the program using the following format: ```/*@CondBounded, y, x1[A1,B1,C1,D1], x2[A2,B2,C2,D2], ...@*/```

### Program examples:

An example of 1-d PCP:
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



An example of Monotone k-d PCP:
```
# this is a comment
int x = -10
int y = 0
while(x < 0){
    {x := x + 1}[1/10]{skip}
    while(y >= 1){
        {y := y - 1}[2/3]{y := y - 2}
    }
    y := y + 10
}
```

An example of Constant k-d PCP:
```
# this is a comment
int T = 0;
int H = 0;
while(T - H > -1){
   {T := T + 1}[9/10]{H := H + 1}
}
```



An example of All But One Counters are Bounded k-d PCP:
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





An example of Conditionally Bounded k-d PCP:
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

More examples can be found in the benchmarks folder.

### Running your own example



### Running (Poetry)
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

### Running (Docker)
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

### Building Artifacts 

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
