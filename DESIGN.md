# Design Goals

## Data-oriented
Starling is designed to facilitate data analysis and processing, including interacting with databases.

# Features

## Planned features

### External data sets
Starling will be capable of handling data sets stored in external files. This includes:
* CSV parsing

### Mathematics
The language will provide several common mathematical functions for convenience, such as:
* Trigonometric functions
* Statistical functions

Starling will also have several builtin data types not commonly found in other languages, including:
* Rational numbers (fractions)
* Complex numbers

### Data structures
Starling will have builtin support for data structures.
Sequence types like arrays (fixed size), vectors (variable size), and matrices will also be available.

### Interfaces
Starling will also feature `interfaces` for laying out methods that should be applicable to structures.

### Functional programming
Starling will facilitate functional programming, including the use of lambda functions and higher-order functions.

### Type enforcement
Variables in Starling will be statically typed. Types are strictly enforced and cannot change at runtime. Variables declared without a type will be assigned a static type at compile time.
Variables must be explicitly converted to the same type before operations can be performed on them, with the exception of Numeric types (`int`, `frac`, `float`) which will be converted implicitly.

### Libraries and Plugins
Starling aims to provide a variety of external libraries available for use. These include:
* Data visualisation tools

# Syntax

## Code blocks
TBD - Blocks use curly brackets `{ }` in the prototype grammar, but this may change.
Variables declared within `if` or `loop` blocks will be accessible outside of the scope of those blocks. Variables declared within function blocks remain within the scope of the function.

## Variable declaration
Variable declaration uses the `var` keyword. The language can infer the type of a variable if one is not given, but an initial value must be provided.
`var foo int = 1;`
`var bar = "foobar";`

## Function declaration
Functions are declared using the `fn` keyword. The language will infer the return type of a function if one is not given.
Parameters of functions are formatted similarly to variable declarations. It's possible to provide a type to be enforced, as well as a default value, though neither are mandatory.
`fn foo(arg type = default) {}`

The foundation of any Starling program is the main function, which will take in a vector of arguments and return an integer:
```
fn main(argv vec) int {
    // Your program here
    return 0;
}
```

## Ranges
Ranges use the syntax `[x:y]`. The lower bound is inclusive and the upper bound is exclusive, as in many other languages.

## Loops
TBD - Starling does not feature traditional `for` loops.
