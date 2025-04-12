# Tasks




- [ ] Parse [PCP](doc/pcp.md) into [Probabilistic transition system](doc/pts.md). The input and the output format are described in the docs. The program should take a `*.pcp` file as an input, and be able to produce a `*.pts.json` file in the specified format. Please pay attention to the <span style="color:blue">DETAILS:</span> text within the documentation. Some tests are available at `src/tests/parse` 

- [ ] Benchmark Collection: please go over [this repository](https://github.com/probing-lab/amber/tree/master/benchmarks) and find all programs containing only one variable. Please convert it to our format, put it to the `src/examples/amber` foler. Also test the parser implementation on the programs. 

- [ ] Implement Guards parsing (future, sketch)
    - [ ] Parse math expression to an AST
    - [ ] Implement Guard analysis: given an AST of a boolean expression find a period and the thresholds after which the guard become periodic

- [ ] Using the pts and the guard analysis extract regular and irregular Markov chains (future, sketch)

- [ ] Analyze irregular MC (future, sketch)
- [ ] Analyze regular MC (future, sketch)
- [ ] Combine the analysis results into an output (future, sketch)





# Design Overview

The overall project structure is as follows, where square boxes represent objexts, arrows and rounded boxes represent algorithms:


![project modules diagram](img/counter-programs-design.drawio.svg)


# Detailed documentation 


- [Probabilistic Counter Programs](doc/pcp.md)
- [Probabilistic Transition System](doc/pts.md)
- [Gruard, Periods, Thresholds](doc/pts.md)
- PBD processes
- Finite State Markov Processes

