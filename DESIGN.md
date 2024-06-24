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
* Rational numbers
* Complex numbers

## Data structures
Starling has builtin support for data structures.
Sequence types like arrays, lists, and matrices are also available.

## Type enforcement
Variables in Starling are statically typed. Types are strictly enforced and cannot change at runtime. Variables declared without a type will be assigned a static type at compile time.
Variables must explicitly be converted to the same type before operations can be performed on them, with the exception of Numeric types (`int`, `rational`, `float`) which are converted implicitly.

## Libraries and Plugins
Starling aims to provide a variety of external libraries available for use. These include:
* Data visualisation tools
