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

## Line termination
Lines of code in Starling are terminated using semicolons `;`.

However, Starling also features semicolon insertion, and will insert a semicolon in place of a newline character, if appropriate.

Semicolons are inserted after any literal, identifier, return statemnt, or closing bracket. Semicolons are **not** inserted anywhere else.

For example, semicolons will **not** be inserted after an operation, an open bracket, or a declaration keyword. This allows code to span multiple lines, for convenience.

## Identifiers
"Identifier" is a collective term which includes the names of variables, functions, structs, and interfaces.

An identifier may contain any alphanumeric character, in addition to underscores. Identifiers may **not** begin with a numeric character.

Examples of valid identifiers include `my_function`, `Number3`, and `_secret`.

Examples of invalid identifiers include `my-function`, `3rdNumber`, and `/secret`.

Reserved keyword names also may not be used as identifiers.

## Data types
Starling currently supports four basic data types. Three of these are numeric: integers `int`, floating point numbers `float`, and fractions `frac`. One is non-numeric: strings `str`.

Starling will not aggressively coerce between data types, and operators can (in general) not be used on different types. For example, this means that a number would need to be explicitly converted into a string in order to perform string operations on it.

### Numeric types

Integer literals are written using only numeric characters. `8` is an `int`.

Floating point literals are written using numeric characters, and contain a decimal point `.`. `3.14` is a `float`.

Fraction literals are written using numeric characters, and contain a double slash `//` to separate the numerator and denominator. `2//5` is a `frac`.

TBD - Fractions may be changed to expressions rather than literals, and thus be made able to take a variable as their numerator and/or denominator. This is not implemented.

TBD - All numeric types will be able to be coerced between each other implicitly, however this is not yet implemented.

### Non-numeric types

Strings are surrounded by double quotes `" "`.

TBD - Single quotes `' '` may be used for a `char` data type, but this is not implemented.

## Operators

Starling features the following basic operators:
* Assignment `=`
* Addition/Concatenation `+`
* Subtraction `-`
* Multiplication `*`
* Division `/`
* Boolean negation `!`
* Equality check `==`
* Inequality check `!=`
* Less than check `<`
* Greater than check `>`
* Less than or equal check `<=`
* Greater than or equal check `>=`

Operators may also be "grouped" using brackets `( )`. This allows the order of operations to be more precisely controlled.

In addition to these, there are some special operations that may be performed on certain types.
* Call `foo(params)` - for callables, such as functions; also used for creating new objects of structs
* Index `foo[index]` - for iterables, such as arrays and vectors
* Selector `foo.bar` `foo.baz(params)` - for accessing attributes or methods of types such as structs

## Code blocks
Blocks will use curly brackets `{ }`.

In general, blocks do not have distinct scope. This includes `if` and `while` blocks.

Function blocks **do** have distinct scope, and variables declared within them **cannot** be accessed outside of the block.

`struct`s, `interface`s, and `impl` declarations also use curly brackets, however these do not function like traditional blocks. See their respective sections of this document for information on their syntax.

## Variable declaration
Variable declaration uses the `var` keyword.

A type and/or an initial value *may* be provided, though neither is required. The type of a variable can be inferred based on either initial or following assignments.

`var foo int = 1;`

`var bar = "foobar";`

`var baz;`

## Function declaration
Functions are declared using the `fn` keyword, in the following form:

```
fn foo() int {
    return 1;
}
```

The `return` keyword is used to provide a value that the function will supply when it is called.

Note also that the return type of the function, here `int`, is placed after the brackets but before the block.

The `void` type is used for functions that have no return value.

```
fn foo() void {
    print("Hello world");
}
```

Like with variables, the language can infer the return type of a function, based on the actual return value, if no type is given.

Parameters of functions are formatted similarly to variable declarations. Parameter types cannot be inferred and must be provided. A default value may also be given for a parameter, but is not required.
`fn foo(arg type = default) {}`

The foundation of any Starling program is the main function, which takes in a vector of arguments and return an integer:
```
fn main(argv vec) int {
    // Your program here
}
```

The main entry point implicitly returns 0, unless an error occurs.

TBD - Starling will also feature "anonymous" or "lambda" functions, but this is not yet implemented.

## If statements
If statments are formed of a condition, an executing block, and an optional else statement. If statments utilise the keywords: `if` and `else`.

```
if true {}
else {}
```

In place of the block following the keywords, any statement can be used. This allows for `else if` structure to be used for multiple conditions.

```
if cond1 {}
else if cond2 {}
else {}
```

## Loops
Starling features `while` loops. Similarly to if statements, these are formed of a condition and an executing block.

```
while true {}
```

TBD - Starling will not feature traditional `for` loops. More discussions need to be had to decide upon the syntax that will be used instead.

## Ranges
Ranges use the syntax `[x:y]`. The lower bound is inclusive and the upper bound is exclusive, as in many other languages.

Ranges only accept integer values for their lower and upper bounds.

Ranges expand to arrays. For example, the range `[1:4]` is equivalent to the array `[1, 2, 3]`.

## Struct declaration
Structs, or structures, are declared with the `struct` keyword.

```
struct Foo {
    bar int;
    ...
}
```

A struct requires one or more fields, separated by semicolons. A type **is** required when declaring a field. A value cannot be provided.
`field str;`

## Interface delaration
Interfaces are declared with the `interface` keyword. An interface requires one or more function signatures to be defined within it, separated by semicolons.

```
interface IO {
    read() str;
    write(value str);
}
```

As interfaces use the same function signature system as function declarations, they follow the same syntax rules. Namely, that types do not *need* to be specified for either function returns or for parameters.

Interfaces are used with the `impl` keyword (see the "Implementing methods on types" heading, below) to add methods to `struct`s in a standardised way. This allows the programmer to ensure that a struct can be operated upon in certain ways.

## Implementing methods on types

The `impl` keyword is used to implement methods for a given type.

It can be used with a bare type. Below is an example using the struct `Foo` described above.
```
impl Foo {
    fn baz() int {
        return self.bar;
    }
}
```

Note the use of the `self` keyword to denote the instance of type `Foo` that the method is being called on.

Only one `impl` block may be created for each bare type per program. It must have the same scope as, and be in the same file as, the type definition (which is usually a `struct`).

The `impl` keyword can also be used in conjunction with an interface. The interface's identifier is given inside a pair of angle brackets `< >`.

The below example demonstrates the type `File` having `IO` methods implemented for it. (See the "Interface declaration" heading, above, for the `IO` interface declaration.)

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

## Optionals

TBD - Not yet implemented.

# Further research required

## Integer precision

The `int` type in Python has infinite precision. It would be good to also implement this in Starling.

We need to research how infinite precision/bit-length integers can be achieved.

## Mathematics

We need to research the best approximations to use for the various standard maths functions that we plan to implement.

The default maths library should have a reasonable degree of precision (3/4 sf?) to ensure that they are efficient.

We may also decide to support another set of maths functions that sacrifice performance in exchange for much higher accuracy, if we believe that it would be beneficial.
