import unittest
from fractions import Fraction

from src.python.lexer import tokenise
from src.python.parser import parse
from src.python.type_checker import TypeChecker
from src.python.interpreter import (
    Interpreter,
    StaObject, StaVariable, StaArray,
    StaStruct, StaFunction, StaFunctionReturn, StaMethod
)
from src.python import ast_nodes as ast
from src.python import builtin
from src.python import type_defs as types
from src.python import cmd


class TestInterpreter(unittest.TestCase):
    global_declrs = """
        struct test_struct_def {x int; y str;}
        var test_struct = test_struct_def(5, \"test\");
        fn test_func(x int) {return x / 2;}
        impl test_struct_def {
            fn foo(x int) int {
                return self.x + x;
            }
        }
        var x int = 1;
    """

    def testing_prerequisites(self):
        cmd.exec_src(self.global_declrs)

    @unittest.expectedFailure
    def test_expr_eval(self):
        tests = {
            "true": StaObject(builtin.types["bool"], True),
            "false": StaObject(builtin.types["bool"], False),
            "2": StaObject(builtin.types["int"], 2),
            "3//2": StaObject(builtin.types["frac"], Fraction(3, 2)),
            "1.5": StaObject(builtin.types["float"], 1.5),
            "\"a\"": StaObject(builtin.types["str"], "a"),
            "!true": StaObject(builtin.types["bool"], False),
            "-1": StaObject(builtin.types["int"], -1),
            "-1//2": StaObject(builtin.types["frac"], Fraction(-1, 2)),
            "1 + 1": StaObject(builtin.types["int"], 2),
            "2 - 1": StaObject(builtin.types["int"], 1),
            "3 * 2": StaObject(builtin.types["int"], 6),
            "3 / 2": StaObject(builtin.types["float"], 1.5),
            # TODO: add more binary expr checks here for different data types
            "[1:4]": StaArray(
                types.ArrayType(builtin.types["int"], 3),
                [
                    StaObject(builtin.types["int"], 1),
                    StaObject(builtin.types["int"], 2),
                    StaObject(builtin.types["int"], 3),
                ],
                3
            ),
            "[1:10][5]": StaObject(builtin.types["int"], 6),
            "test_struct.x": StaObject(builtin.types["int"], 5),
            "test_struct.y": StaObject(builtin.types["str"], "test"),
            "test_func(5)": StaObject(builtin.types["float"], 2.5),
            "test_struct.foo(1)": StaObject(builtin.types["int"], 6),
        }

        for test, expected in tests.items():
            test = self.global_declrs + "fn test() {return " + test + ";}"
            with self.subTest(test=test):
                res = cmd.exec_src(test, entry_name="test")
                self.assertEqual(res, expected)

    def test_stmt_eval(self):
        tests = {
            "if true {return 1;} else {return 0;}": StaObject(
                builtin.types["int"], 1
            ),
            "if false {return 1;} else {return 0;}": StaObject(
                builtin.types["int"], 0
            ),
            "while x < 10 {x = x * 2;} return x;": StaObject(
                builtin.types["int"], 16
            ),
            "x = 10; return x;": StaObject(
                builtin.types["int"], 10
            ),
        }

        for test, expected in tests.items():
            test = self.global_declrs + "fn test() {" + test + "}"
            with self.subTest(test=test):
                res = cmd.exec_src(test, entry_name="test")
                self.assertEqual(res, expected)

    def test_declr_eval(self):
        tests = {
            "fn test() int {}": StaFunction(
                types.FunctionType(builtin.types["int"], []),
                "test",
                [],
                ast.Block([]),
            ),
            "struct test {x int; y str;}": types.StructType(
                "test",
                {
                    "x": builtin.types["int"],
                    "y": builtin.types["str"],
                },
            ),
            "var test float = 3.14;": StaVariable(
                "test",
                StaObject(builtin.types["float"], 3.14),
            ),
            "interface test {x() int; y(z str) str;}": types.Interface(
                "test",
                {
                    "x": types.FunctionType(
                        builtin.types["int"],
                        [],
                    ),
                    "y": types.FunctionType(
                        builtin.types["str"],
                        [
                            builtin.types["str"]
                        ],
                    ),
                },
            ),
            """struct test {x int;}
               impl test {fn foo() int {}}""": types.StructType(
                "test",
                {
                    "x": builtin.types["int"]
                },
                methods={
                    "foo": StaMethod(
                        types.FunctionType(
                            builtin.types["int"],
                            []
                        ),
                        "foo",
                        [],
                        ast.Block([]),
                        None
                    ),
                },
            ),
            """struct foo {x int; y str;}
               var test = foo(5, "test");""": StaVariable(
                "test",
                StaStruct(
                    types.StructType(
                        "foo",
                        {
                            "x": builtin.types["int"],
                            "y": builtin.types["str"],
                        }
                    ),
                    "foo",
                    {
                        "x": StaVariable(
                            "x",
                            StaObject(builtin.types["int"], 5)
                        ),
                        "y": StaVariable(
                            "y",
                            StaObject(builtin.types["str"], "test")
                        ),
                    }
                ),
            ),
        }

        for test, expected in tests.items():
            with self.subTest(test=test):
                tokens = tokenise(test)
                tree = parse(tokens)
                tc = TypeChecker(tree)
                tc.check(tree)
                interpreter = Interpreter()
                interpreter.eval_node(tree)
                self.assertEqual(interpreter.scope.lookup("test"), expected)
