# Compiler for a simple imperative language

## Short description of the language an its compilation

Language operates on natural numbers and supports the following functionality:
- arithmetic operations(+, -, *, /, %), relations(==, !=, <, >, <=, >=)
- variable assignment, tabels, memory management
- various loops, if else conditions
- error handling with indication of the occurrence location and type, comments
- post-compilation mchine code optimization

## Installation
The compiler was implemented in Python 3 with use of PLY

To run the compiler, you need to type the following commands:
```bash
sudo apt update
sudo apt install python3
sudo apt install python3-pip
pip3 install ply
```

## Usage
The compilation is executed with the following command:

```bash
python3 compiler.py <input_file> <output_file>
```
<input_file> - should include some program wrote in our language  
<output_file> - will contain machine code after compiling the code from the input

## Similar copmilation problem

### Language grammar

![image](https://i.imgur.com/A6XVV5l.png)

### Machine code

| Command | Interpretation | Time |
|---------|----------------|------|
| GET X   | stores the fetched number in register r<sub>X</sub> and k ← k + 1 | 100 |
| PUT X   | displays the contents of register r<sub>X</sub> and k ← k + 1 | 100 |
| LOAD X  | r<sub>X</sub> ← p<sub>r<sub>A</sub></sub> and k ← k + 1 | 50 |
| STORE X | p<sub>r<sub>A</sub></sub> ← r<sub>X</sub> and k ← k + 1 | 50 |
| COPY Y X | r<sub>X</sub> ← r<sub>Y</sub> and k ← k + 1 | 5 |
| ADD X Y | r<sub>X</sub> ← r<sub>X</sub> + r<sub>Y</sub> and k ← k + 1 | 5 |
| SUB X Y | r<sub>X</sub> ← max{r<sub>X</sub> - r<sub>Y</sub>, 0} and k ← k + 1 | 5 |
| HALF X  | r<sub>X</sub> ← [r<sub>X</sub>/2] and k ← k + 1 | 1 |
| INC X   | r<sub>X</sub> ← r<sub>X</sub> + 1 and k ← k + 1 | 1 |
| DEC X   | r<sub>X</sub> ← max(r<sub>X</sub> - 1, 0) and k ← k + 1 | 1 |
| JUMP j  | k ← j | 1 |
| JZERO X j | if r<sub>X</sub> = 0 then k ← j, else k ← k + 1 | 1 |
| JODD X j | if r<sub>X</sub> is odd then k ← j, else k ← k + 1 | 1 |
| HALT    | stop the program | 0 |

X, Y ∈ {A, B, C, D, E, F, G, H}

### Compilation example

![image](https://i.imgur.com/KUuIp6O.png)
