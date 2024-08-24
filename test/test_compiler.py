import unittest

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
        cmd.compile_src(self.global_declrs)

    def test_expr_eval(self):
        tests = {
            "true": 1,
            "false": 0,
            "2": 2,
            "3//2": None,
            "1.5": 1.5,
            "\"a\"": "a",
            "!true": 0,
            "-1": -1,
            "-1//2": None,
            "1 + 1": 2,
            "2 - 1": 1,
            "3 * 2": 6,
            "3 / 2": 1.5,
            # TODO: add more binary expr checks here for different data types
            "[1:4]": None,
            "[1:10][5]": 6,
            "test_struct.x": 5,
            "test_struct.y": "test",
            "test_func(5)": 2.5,
            "test_struct.foo(1)": 6,
        }

        for test, expected in tests.items():
            test = self.global_declrs + "fn test() {return " + test + ";}"
            with self.subTest(test=test):
                res = cmd.compile_src(test, entry_name="test")
                self.assertEqual(res, expected)

    def test_stmt_eval(self):
        tests = {
            "if true {return 1;} else {return 0;}": 1,
            "if false {return 1;} else {return 0;}": 0,
            "while x < 10 {x = x * 2;} return x;": 16,
            "x = 10; return x;": 10,
        }

        for test, expected in tests.items():
            test = self.global_declrs + "fn test() {" + test + "}"
            with self.subTest(test=test):
                res = cmd.compile_src(test, entry_name="test")
                self.assertEqual(res, expected)
