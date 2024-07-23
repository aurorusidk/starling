# Design Goals

## Data-oriented
Starling is designed to facilitate data analysis and processing, including interacting with databases.

# Features

## Planned features

### External data sets
Starling will be capable of handling data sets stored in external files. This includes:
* CSV files
* Spreadsheets
* XML and YAML markup files
* JSON files
* Databases

### Mathematics
The language will provide several common mathematical functions for convenience, such as:
* Trigonometric functions
* Statistical functions

Starling will also have several builtin data types not commonly found in other languages, including:
* Rational numbers (fractions)
* Complex numbers

### Data structures
Starling will have builtin support for data structures.
Sequence types like arrays (fixed size), vectors (variable size), dictionaries, hash maps, and matrices will also be available.

### Interfaces
Starling will also feature `interface`s for laying out methods that should be applicable to structures.

Core sequence data structures will be members of the `iterable` interface.

### Functional programming
Starling will facilitate functional programming, including the use of lambda functions and higher-order functions.

### Type enforcement
Variables in Starling will be statically typed. Types will be strictly enforced and cannot change at runtime. Variables declared without a type will be assigned a static type at compile time.

Variables must be explicitly converted to the same type before operations can be performed on them, with the exception of Numeric types (`int`, `frac`, `float`) which will be converted implicitly.

### Optional values
Starling will make use of an `Optional` generic type, akin to that found in Rust.

The value held in an Optional must be specifically retrieved before use, including handling if that value is `None`.

### Errors & Results
Starling will also have a `Result` generic type, which will make use of `Optional`s to provide error information.

The `Result` type will be defined as follows:

```
struct Result<T> {
    ok Optional<T>
    err Optional<Error>
}
```

### Libraries and Plugins
Starling aims to provide a variety of external libraries for use with the core language. These may include:
* Data visualisation tools
* More niche data structures such as queues, deques, and stacks

# Syntax

## Code blocks
Blocks will use curly brackets `{ }`.

Variables declared within `if` or `loop` blocks will be accessible outside of the scope of those blocks. Variables declared within function blocks remain within the scope of the function.

## Variable declaration
Variable declaration uses the `var` keyword. The language can infer the type of a variable if one is not given, but an initial value must be provided.

`var foo int = 1;`

`var bar = "foobar";`

For assignment expressions, the `:=` operator will be used.

## Function declaration
Functions are declared using the `fn` keyword. The language will infer the return type of a function if one is not given.

The `void` type is used for functions that have no return value.

Parameters of functions are formatted similarly to variable declarations. It's possible to provide a type to be enforced, as well as a default value, though neither are mandatory.
`fn foo(arg type = default) {}`

The foundation of any Starling program is the main function, which will take in a vector of arguments and return an integer:
```
fn main(argv vec) int {
    // Your program here
}
```

The main entry point implicitly returns 0, unless an error occurs.

## Optionals
The below example function returns 1 if `true` is passed in, and returns no value if `false` is passed in.

```
fn optional_func(x bool) Optional<int> {
    if (x) {
        return some(1)
    } else {
        return nil
    }
}
```

The value of a `some()` return must match the type specified in the `Optional<>`. So you can't put a rat in a headphone box.

The return value of an optional can be handled as follows:

```
var ret_val Optional<int> = optional_func(true)
if (ret_val.is_some()) {
    print(ret_val.unbox())
} 
```

`unbox()` will error if the value is `nil`.

## Ranges
Ranges use the syntax `[x:y]`. The lower bound is inclusive and the upper bound is exclusive, as in many other languages.

## Loops
TBD - Starling does not feature traditional `for` loops.

# Further research required

## Mathematics

We need to research the best approximations to use for the various standard maths functions that we plan to implement.

The default maths library should have a reasonable degree of precision (3/4 sf?) to ensure that they are efficient.

We may also decide to support another set of maths functions that sacrifice performance in exchange for much higher accuracy, if we believe that it would be beneficial.
