

# Pastry: the Positive AST pRototYpe

Pastry is an academic prototype for deciding (positive) Almost-Sure Termination of essentially 1-d probabilistic counter programs (PCPs).

## Contents
- [Project Structure](#project-structure)
- [Requirements](#requirements)
- [Setup](#setup)
- [Smoke test](#smoke-test)
- [Replicating the results from the paper](#replicating-the-results-from-the-paper)
- [Running Pastry on benchmarks](#running-pastry-on-benchmarks)
- [Writing your own example](#writing-your-own-example)
- [Running Pastry on your own example](#running-pastry-on-your-own-example)

## Project Structure
The structure of the artifact is as follows.

```bash
/home/artifact
├── benchmarks        # benchmarks that are konwn unsupported by a tool are excluded from the corresponding directory
│   ├── pastry
│   ├── amber
│   ├── KoAT1
│   └── KoAT2
├── pastry     
│   ├── outputs
│   ├── test   
│   └── src          
├── baselines          
├── ├── amber           
├── ├── KoAT1
├── └── KoAT2  
└── ...            
```

## Requirements
- Install Docker (https://www.docker.com/get-started/) in case you do not have it yet.
- Experiments in the paper are conducted on a 3.22 GHz Apple M1 Pro processor with 16GB RAM running macOS Sonoma. Make sure to have similar specs when comparing timing results and consider differences running in a sandbox (docker).



## Setup
To create a docker container from the provided tar file:
```bash
docker load -i pastry.tar
```

## Smoke test

For a quick test to see if everything works:

```bash
docker run --rm --entrypoint bash pastry:latest pastry/batch_test.sh --input \
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


## Replicating the results from the paper

Reproduce the Table 1 presented in the paper by typing (take ~7mins):

```bash
./run.sh --run-all -t 90
```

```bash
docker run --rm -it -v "$(pwd)/outputs:/home/artifact/pastry/outputs" -v "$(pwd)/result:/home/artifact/result" --entrypoint bash pastry:latest run.sh --run-all -t 90
```
or on Windows PowerShell, run this command:
```bash
docker run --rm -it -v "$(Get-Location)/outputs:/home/artifact/pastry/outputs" -v "$(Get-Location)/result:/home/artifact/result" --entrypoint bash pastry:latest run.sh --run-all -t 90
```

The result in CSV format can be found in '/home/artifact/result'.


## Running Pastry on benchmarks

To run the benchmark suite, run:
```bash
docker run --rm -v "$(pwd)/outputs:/home/artifact/pastry/output" --entrypoint bash pastry:latest pastry/benchmark.sh 
```
or on Windows PowerShell, run this command:
```bash
docker run --rm -v "$(Get-Location)/outputs:/home/artifact/pastry/output" --entrypoint bash pastry:latest pastry/benchmark.sh 
```

To run Pastry on a specific benchmark (for example, 2d_bounded_rw):

```bash 
docker run --rm -v "$(pwd)/outputs:/home/artifact/pastry/outputs" --entrypoint bash pastry:latest run.sh pastry 2d_bounded_rw
```
or on Windows PowerShell, run this command:
```bash 
docker run --rm -v "$(Get-Location)/outputs:/home/artifact/pastry/outputs" --entrypoint bash pastry:latest run.sh pastry 2d_bounded_rw
```
The detailed logs will be available in '/home/artifact/pastry/outputs'.


## Writing your own example

This section describes the input language used by Pastry and how users can write, annotate their own probabilistic counter programs, along with example programs illustrating the format.


### Program syntax rules


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

expression: var                                  -> var
            | INT                                 -> int
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
        | "Ne" "(" expression "," expression ")" -> neq
        | guard "&" guard                        -> and
        | guard "|" guard                        -> or
        | "Not" "(" guard ")"                    -> not

literal: INT     -> int
        | NAT    -> nat         
        | POSINT -> pos_int      
        | PROB   -> prob         

var: CNAME
```




**Note:** Direct assignment format like `var := c` are not allowed. Instead, use two consecutive counter-style loops to simulate the direct assignment `var := c`:
    ``` 
    while (var < c) { var := var + 1 }
    while (var > c) { var := var - 1 }
    ```

### Annotation rules
In addition to 1-d PCPs, Pastry also supports verification for four classes of k-d PCPs: Monotone PCPs, Constant PCPs, All But One Counters are Bounded PCPs, and Conditionally Bounded PCPs. For Monotone PCPs and Constant PCPs, Pastry supports automated checking of whether an input k-d PCP belongs to these categories and thus perform verification without any user's hint. However, For **All But One Counters are Bounded PCPs** and **Conditionally Bounded PCPs**, users are required to provide correct annotations to assist the analysis：
- For **All But One Counters are Bounded PCPs**, users are required to annotate the unbounded variable and the closed intervals for other variables at the top of the program using the following format: ```/*@Bounded, <unbounded_var>, <var1>[<lower>,<upper>], <var2>[<lower>,<upper>], ...@*/```. If all variable are bounded, the ```<unbounded_var>``` can be omitted from the annotation: ```/*@Bounded, <var1>[<lower>,<upper>], <var2>[<lower>,<upper>], ...@*/```
- For **Conditionally Bounded PCPs**, users are required to provide coefficient information at the top of the program using the following format: ```/*@CondBounded, y, x1[A1,B1,C1,D1], x2[A2,B2,C2,D2], ...@*/```

### Program examples

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

## Running Pastry on your own example

Suppose you saved your example in a file named `xxx.txt` in the path /home/artifact/benchmarks/pastry. Then the tool can be run as:


```bash
bash exec.sh pastry xxx
```

