# Design Goals

## Data-oriented
Starling is designed to facilitate data analysis and processing, including interacting with databases.

# Features

## External data sets
Starling is capable of handling data sets stored in external files. This includes:
* CSV parsing

## Mathematics
The language provides several common mathematical functions for convenience, such as:
* Trigonometric functions
* Statistical functions

Starling also has several builtin data types not commonly found in other languages, including:
* Rational numbers (fractions)
* Complex numbers

## Data structures
Starling has builtin support for data structures.
Sequence types like arrays (fixed size), vectors (variable size), and matrices are also available.

## Functional programming
Starling facilitates functional programming, including the use of lambda functions and higher-order functions.

## Type enforcement
Variables in Starling are statically typed. Types are strictly enforced and cannot change at runtime. Variables declared without a type will be assigned a static type at compile time.
Variables must be explicitly converted to the same type before operations can be performed on them, with the exception of Numeric types (`int`, `frac`, `float`) which are converted implicitly.

## Libraries and Plugins
Starling aims to provide a variety of external libraries available for use. These include:
* Data visualisation tools

# Syntax

## Code blocks
TBD - Blocks use curly brackets `{ }` in the prototype grammar, but this may change.
Variables declared within `if` or `loop` blocks are accessible outside of the scope of those blocks. Variables declared within function blocks remain within the scope of the function.

## Variable declaration
Variable declaration uses the `var` keyword. The language can infer the type of a variable if one is not given, but an initial value must be provided.
`var foo int = 1;`
`var bar = "foobar";`

## Function declaration
Functions are declared using the `fn` keyword. The language can infer the return type of a function if one is not given.

The foundation of any Starling program is the main function, which takes in a vector of arguments and returns an integer:
```
fn main(vec argv) int {
    // Your program here
    return 0;
}
```

## Ranges
Ranges use the syntax `[x:y]`. The lower bound is inclusive and the upper bound is exclusive, as in many other languages.

## Loops
TBD - Starling does not feature traditional `for` loops.
