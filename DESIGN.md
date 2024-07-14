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

`var foo int = 1`

`var bar = "foobar"`

For assignment expressions, the `:=` operator will be used.

## Function declaration
Functions are declared using the `fn` keyword. The language will infer the return type of a function if one is not given.

Parameters of functions are formatted similarly to variable declarations. It's possible to provide a type to be enforced, as well as a default value, though neither are mandatory.
`fn foo(arg type = default) {}`

The foundation of any Starling program is the main function, which will take in a vector of arguments and return an integer:
```
fn main(argv vec) int {
    // Your program here
}
```

The main entry point implicitly returns 0, unless an error occurs.

## Struct declaration
Structs, or structures, are declared with the `struct` keyword.

```
struct Foo {
    bar int,
    ...
}
```

A struct requires one or more fields, separated by commas. A field is simply an uninitialised variable.
`field str`

## Interface delaration
Interfaces are declared with the `interface` keyword. An interface requires one or more function signatures to be defined within it.

```
interface IO {
    read() str,
    write(value str)
}
```

## Implementing methods on types

The `impl` keyword is used to implement methods for a given type.

It can be used with a bare type. Below is an example using the struct `Foo` described above.
```
impl Foo {
    fn baz() int {
        return self.bar
    }
}
```

Note the use of the `self` keyword to denote the instance of type `Foo` that the method is being called on.

Only one `impl` block may be created for each bare type per program. It must have the same scope as, and be in the same file as, the type definition (which is usually a `struct`).

The `impl` keyword can also be used in conjunction with an interface. The interface's identifier is given inside a pair of angle brackets `< >`.

The below example demonstrates the type `File` having `IO` methods implemented for it. (See the interface declaration heading, above, for the `IO` interface declaration.)

```
struct File {
    filename,
    contents,
    length,
    metadata
}

impl File<IO> {
    fn read() {
        return self.contents
    }

    fn write(value) {
        self.contents = value
    }
}
```

All methods of an `interface` must be implemented within a single `impl` block for a given type.

Interfaces can be implemented on types declared in other files, but the `impl` block must still have the same scope as the type definition.

## Ranges
Ranges use the syntax `[x:y]`. The lower bound is inclusive and the upper bound is exclusive, as in many other languages.

## Loops
TBD - Starling will not feature traditional `for` loops.

# Further research required

## Mathematics

We need to research the best approximations to use for the various standard maths functions that we plan to implement.

The default maths library should have a reasonable degree of precision (3/4 sf?) to ensure that they are efficient.

We may also decide to support another set of maths functions that sacrifice performance in exchange for much higher accuracy, if we believe that it would be beneficial.

## No nulls

We need to research how languages such as R and Rust are able to have no `null` value, and decide whether we want to implement one in Starling.

We then also need to decide what the names should be for the null value and type.
