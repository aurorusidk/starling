import unittest
from fractions import Fraction

from src.python.interpreter import StaObject, StaArray
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
