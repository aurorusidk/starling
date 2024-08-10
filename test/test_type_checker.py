import unittest
from src.python.lexer import tokenise
from src.python.parser import Parser
from src.python.ir import IRNoder
from src.python.type_checker import TypeChecker
from src.python import builtin
from src.python import type_defs as types


class TestTypeChecker(unittest.TestCase):
    global_declrs = [
        "var x int;",
        "fn test(n float) frac {}",
    ]

    def testing_prerequisites(self, noder=None):
        for declr in self.global_declrs:
            tokens = tokenise(declr)
            ast = Parser(tokens).parse(tokens)
            if noder is None:
                # for when this is run as a test
                noder = IRNoder()
            iir = noder.make(ast)
            tc = TypeChecker(iir)
            tc.check(iir)

    @unittest.expectedFailure
    def test_valid_expr_check(self):
        tests = {
            "1 + 1": builtin.types["int"],
            "1 + 1//2": builtin.types["frac"],
            "1 + 1.5": builtin.types["float"],
            "\"a\" + \"b\"": builtin.types["str"],
            "3 / 2": builtin.types["float"],  # in tc should this be rational?
            "x + 1": builtin.types["int"],
            "x * 0.5": builtin.types["float"],
            "!true": builtin.types["bool"],
            "[1:10][0]": builtin.types["int"],
            "[0:x + 1][x]": builtin.types["int"],
            "test(1.5)": builtin.types["frac"],
            "test(x + 0.5)": builtin.types["frac"],
        }

        for test, expected in tests.items():
            tokens = tokenise(test)
            ast = Parser(tokens).parse_expression()
            noder = IRNoder()
            self.testing_prerequisites(noder)
            iir = noder.make(ast)
            tc = TypeChecker()
            tc.check(iir)
            self.assertEqual(iir.checked_type, expected)

    @unittest.expectedFailure
    def test_invalid_expr_check(self):
        tests = [
            "1 + \"a\"",
            "\"a\" * \"b\"",
            "true / false",
            "x - \"a\"",
            "test(x)",
            "test(1, 2)",
            "test(\"foo\")",
            "test(1.5)[x]",
            "[1:10][1.5]",
            "[0:4.5]",
            "!1.5",
            "-\"a\"",
        ]

        for test in tests:
            tokens = tokenise(test)
            ast = Parser(tokens).parse_expression()
            noder = IRNoder()
            self.testing_prerequisites(noder)
            iir = noder.make(ast)
            tc = TypeChecker()
            self.assertRaises(AssertionError, tc.check, iir)

    def test_valid_stmt_check(self):
        tests = [
            "if x == 1 {} else {}",
            "while x > 0 {}",
            "return 1//2;",
            "x = 1;",
        ]

        for test in tests:
            tokens = tokenise(test)
            ast = Parser(tokens).parse_statement()
            noder = IRNoder()
            self.testing_prerequisites(noder)
            noder.current_func = noder.scope.lookup("test")
            noder.make(ast)
            tc = TypeChecker()
            tc.check(noder.block)

    def test_invalid_stmt_check(self):
        tests = [
            "if x {} else {}",
            "if 1 {}",
            "while x {}",
            "return 1.5;",
            "return x;",
            "x = 1//2;",
            "x = \"test\";",
        ]

        for test in tests:
            tokens = tokenise(test)
            ast = Parser(tokens).parse_statement()
            noder = IRNoder()
            block = noder.block
            self.testing_prerequisites(noder)
            noder.current_func = noder.scope.lookup("test")
            noder.make(ast)
            tc = TypeChecker()
            self.assertRaises(AssertionError, tc.check, block)

    @unittest.expectedFailure
    def test_valid_declr_check(self):
        tests = {
            "fn test(x float) frac {}": types.FunctionType(
                builtin.types["frac"],
                [
                    builtin.types["float"],
                ]
            ),
            "struct test {x int; y str;}": types.StructType(
                {
                    "x": builtin.types["int"],
                    "y": builtin.types["str"],
                }
            ),
            "var test int = 1;": builtin.types["int"],
        }

        for test, expected, in tests.items():
            tokens = tokenise(test)
            ast = Parser(tokens).parse_declaration()
            noder = IRNoder()
            noder.make(ast)
            tc = TypeChecker()
            tc.check(noder.block)
            self.assertEqual(noder.scope.lookup("test").checked_type, expected)

    def test_invalid_declr_check(self):
        tests = [
            # TODO: are there any other possible errors here?
            "var test str = 1.5;",
        ]

        for test in tests:
            tokens = tokenise(test)
            ast = Parser(tokens).parse_declaration()
            noder = IRNoder()
            noder.make(ast)
            tc = TypeChecker()
            self.assertRaises(AssertionError, tc.check, noder.block)

    @unittest.expectedFailure
    def test_valid_inference(self):
        tests = {
            "var test = 1;": builtin.types["int"],
            "var test = 5/2;": builtin.types["float"],
            "var test = 1 + 1.5;": builtin.types["float"],
            "var test = \"a\";": builtin.types["str"],
            "var test = true;": builtin.types["bool"],
            "var test = \"true\";": builtin.types["str"],
            "var test = 5//2;": builtin.types["frac"],
            """fn test(x int) {
                    return x + 1
                }
            """: types.FunctionType(
                builtin.types["int"],
                [
                    builtin.types["int"],
                ]
            ),
            """fn test(x int) {
                    return x + 2.5
                }
            """: types.FunctionType(
                builtin.types["float"],
                [
                    builtin.types["int"],
                ]
            ),
            """fn test() {
                    return "a"
                }
            """: types.FunctionType(
                builtin.types["str"], []),
        }
        # TODO: add type inference between numeric types for a single var
        #        (i.e. like the first tests for invalid, but for int to float)

        for test, expected, in tests.items():
            tokens = tokenise(test)
            ast = Parser(tokens).parse_declaration()
            noder = IRNoder()
            noder.make(ast)
            tc = TypeChecker()
            tc.check(noder.block)
            self.assertEqual(noder.scope.lookup("test").checked_type, expected)

    def test_invalid_inference(self):
        tests = [
            """fn test() {
            var x;
            x = 1;
            x="a";
            }
            """,
            """fn test() {
            var x;
            x = true;
            x="true";
            }
            """,
            """fn test() {
            var x;
            x = 1.5;
            x= "1.5";
            }
            """,
            """fn test(x int) {
                if x == 1 {
                return 1
                }
                else {
                return 1.5
                }
            }
            """,
            """fn test(x int) {
                if x == 1 {
                return 1
                }
                else {
                return "a"
                }
            }
            """,
            """fn test(x int) {
                if x == 1 {
                return true
                }
                else {
                return "true"
                }
            }
            """,
        ]

        for test in tests:
            tokens = tokenise(test)
            ast = Parser(tokens).parse_declaration()
            noder = IRNoder()
            noder.make(ast)
            tc = TypeChecker()
            self.assertRaises(AssertionError, tc.check, noder.block)
