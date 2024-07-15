![Starling](https://github.com/aurorusidk/starling/assets/75564966/44fc3567-5188-4c5d-97ee-b724e3301b94)

Starling is a high-level programming language designed for data processing.

# Requirements
## Python (Prototyping) Implementation:
* Python 3
* llvmlite

## Zig Implementation:
* Zig
* LLVM

# Design
[Read more about the design and features of the language](./DESIGN.md)

# Roadmap
## Bootstrap
This will likely be done only in Python as a simple starting point.

- [x] Prototype grammar
- [x] Lexer
- [x] Parser
- [x] Basic codegen (maybe just an interpreter)

## Initial Design
- [x] Create language design goals
- [x] Determine necessary features and main focuses
- [x] Begin language grammar
- [x] Implement new grammar features into lexer and parser
- [ ] Codegen framework and support for different backends (compiled/interpreted)
    - [x] Interpreter
    - [ ] Compiler
- [ ] Testing suite
    - [x] Lexer Tests
    - [x] Parser Tests
    - [x] Type Checker Tests
    - [x] Interpreter Tests
    - [ ] Compiler Tests
- [ ] Zig implementation
- [ ] Feature Implementation

## Built-in and Plug-in Features
- [ ] Data Set Handling
    - [ ] CSV
    - [ ] Spreadsheet
    - [ ] XML/YAML
    - [ ] JSON
    - [ ] Database
- [ ] Mathematical Functionality
    - [ ] Trignometric Functions
    - [ ] Statistical Functions
    - [ ] Rational Number Handling
    - [ ] Complex Number Handling
- [ ] Visualisation Tools
    - [ ] Graphing
        - [ ] ...
- [ ] Data Structures (?)
