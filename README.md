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
- [x] Create initial language design goals
- [x] Create initial roadmap
- [x] Language grammar
- [x] Codegen framework and support for different backends (compiled/interpreted)
    - [x] Intemediate Representation (IR)
    - [x] Interpreter
    - [x] Compiler
- [x] Testing suite
    - [x] Lexer Tests
    - [x] Parser Tests
    - [x] IR Testing
    - [x] Type Checker Tests
    - [x] Interpreter Tests
    - [x] Compiler Tests
- [ ] Base Feature Implementation
    - [x] Variables
    - [x] Functions
    - [x] Structures
    - [x] Interfaces
    - [x] Methods/Impls
    - [ ] Arrays/Vectors
    - [ ] Strings

## Core Development
- [ ] Import System
- [ ] Errors
- [ ] Optionals/nil
- [ ] Generic Typing
- [ ] Functions as expressions
- [ ] Higher-Order Functions
- [ ] Standard Library
- [ ] Zig implementation

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
    - [ ] Randomness
- [ ] Visualisation Tools
    - [ ] Graphing
    - [ ] Flowcharts
    - [ ] Schematics
- [ ] Extended Data Structures
    - [ ] Deques
    - [ ] Queues
    - [ ] Linked Lists
- [ ] System API
    - [ ] File System
    - [ ] Processes
    - [ ] System Info
