import unittest
from src.python.cmd import translate


class TestTypeChecker(unittest.TestCase):
    def test_globals(self):
        # TODO: add interfaces once fully implemented
        tests = {
            "fn main() {}": (
                "1:\n"
                " DECLARE main() #2 [fn () -> nil]\n"
                "2:\n"
                " [empty]"
            ),
            """
            fn test() {}
            fn main() {}
            """: (
                "1:\n"
                " DECLARE test() #2 [fn () -> nil]\n"
                " DECLARE main() #3 [fn () -> nil]\n"
                "2:\n"
                " [empty]\n"
                "3:\n"
                " [empty]"
            ),
            """
            struct test {
                a int;
            }
            """: (
                "1:\n"
                " DECLARE test{a} [struct {int}]"
            ),
        }

        for test, expected in tests.items():
            with self.subTest(test=test):
                self.assertEqual(translate(test, typecheck=True, test=True), expected)

    def test_valid_ref(self):
        tests = {
            """
            struct test {
                a int;
            }

            fn main() {
                var b test;
                var c = b.a;
            }
            """: (
                "1:\n"
                " DECLARE test{a} [struct {int}]\n"
                " DECLARE main() #2 [fn () -> nil]\n"
                "2:\n"
                " DECLARE b [test{a}]\n"
                " DECLARE c [int]\n"
                " ASSIGN c [int] <- LOAD(b.a [int]) [int]"
            ),
            """
            fn test() {
            }

            fn main() {
                test();
            }
            """: (
                "1:\n"
                " DECLARE test() #2 [fn () -> nil]\n"
                " DECLARE main() #3 [fn () -> nil]\n"
                "2:\n"
                " [empty]\n"
                "3:\n"
                " CALL test() #2 [fn () -> nil] ()"
            ),
        }

        for test, expected in tests.items():
            with self.subTest(test=test):
                self.assertEqual(translate(test, typecheck=True, test=True), expected)

    def test_valid_instr(self):
        # check while loops
        tests = {
            "var a;": (
                "1:\n"
                " DECLARE main() #2 [fn () -> nil]\n"
                "2:\n"
                " DECLARE a"
            ),
            "var a; var b = a;": (
                "1:\n"
                " DECLARE main() #2 [fn () -> nil]\n"
                "2:\n"
                " DECLARE a\n"
                " DECLARE b\n"
                " ASSIGN b <- LOAD(a)"
            ),
            "var a; a = 5;": (
                "1:\n"
                " DECLARE main() #2 [fn () -> nil]\n"
                "2:\n"
                " DECLARE a [int]\n"
                " ASSIGN a [int] <- 5 [int]"
            ),
            "return 0;": (
                "1:\n"
                " DECLARE main() #2 [fn () -> int]\n"
                "2:\n"
                " RETURN 0 [int]"
            ),
            "if true return 0;": (
                "1:\n"
                " DECLARE main() #2 [fn () -> int]\n"
                "2:\n"
                " CBRANCH True [bool] #3 #4\n"
                "3:\n"
                " RETURN 0 [int]\n"
                "4:\n"
                " [empty]"
            ),
            "var x int; while x > 0 {}": (
                "1:\n"
                " DECLARE main() #2 [fn () -> nil]\n"
                "2:\n"
                " DECLARE x [int]\n"
                " BRANCH #3\n"
                "3:\n"
                " CBRANCH (LOAD(x [int]) [int] > 0 [int]) [bool] #4 #5\n"
                "4:\n"
                " BRANCH #3\n"
                "5:\n"
                " [empty]"
            ),
            "fn test() {}": (
                "1:\n"
                " DECLARE main() #2 [fn () -> nil]\n"
                "2:\n"
                " DECLARE test() #3 [fn () -> nil]\n"
                "3:\n"
                " [empty]"
            ),
            "var a = 5; a = a + 5;": (
                "1:\n"
                " DECLARE main() #2 [fn () -> nil]\n"
                "2:\n"
                " DECLARE a [int]\n"
                " ASSIGN a [int] <- 5 [int]\n"
                " ASSIGN a [int] <- (LOAD(a [int]) [int] + 5 [int]) [int]"
            ),
        }

        for test_contents, expected in tests.items():
            test = "fn main() {" + test_contents + "}"
            with self.subTest(test=test):
                self.assertEqual(translate(test, typecheck=True, test=True), expected)

    def test_valid_expr_check(self):
        tests = {
            "a = 1 + 1": (
                " DECLARE a [int]\n"
                " ASSIGN a [int] <- (1 [int] + 1 [int]) [int]"
            ),
            "a = \"a\" + \"b\"": (
                " DECLARE a [str]\n"
                " ASSIGN a [str] <- ([a] [str] + [b] [str]) [str]"
            ),
            "a = 3 / 2": (
                " DECLARE a [float]\n"
                " ASSIGN a [float] <- (3 [int] / 2 [int]) [float]"
            ),  # in tc should this be rational?
            "var x int; a = x + 1": (
                " DECLARE a [int]\n"
                " DECLARE x [int]\n"
                " ASSIGN a [int] <- (LOAD(x [int]) [int] + 1 [int]) [int]"
            ),
            "a = !true": (
                " DECLARE a [bool]\n"
                " ASSIGN a [bool] <- !True [bool] [bool]"
            ),
        }

        for test_contents, expected_contents in tests.items():
            test = "fn main() { var a; " + test_contents + ";}"
            expected = (
                "1:\n"
                " DECLARE main() #2 [fn () -> nil]\n"
                "2:\n"
            ) + expected_contents
            with self.subTest(test=test):
                self.assertEqual(translate(test, typecheck=True, test=True), expected)

    def test_invalid_expr_check(self):
        tests = [
            "1 + \"a\"",
            "\"a\" * \"b\"",
            "true / false",
            "x - \"a\"",
            "!1.5",
            "-\"a\"",
        ]

        for test_contents in tests:
            test = "fn main() { var a; " + test_contents + ";}"
            with self.subTest(test=test):
                self.assertRaises(AssertionError, translate, test, typecheck=True, test=True)

    def test_invalid_stmt_check(self):
        tests = [
            "if x {} else {}",
            "if 1 {}",
            "while x {}",
            "while 7 {}",
            "return x;",
        ]

        for test_contents in tests:
            test = "fn main() {" + test_contents + "}"
            with self.subTest(test=test):
                self.assertRaises(AssertionError, translate, test, typecheck=True, test=True)

    def test_invalid_declr_check(self):
        tests = [
            "var x int = 1//2;",
            "var x int = \"test\";",
            "var a int; var b bool = a;",
        ]

        for test_contents in tests:
            test = "fn main() {" + test_contents + "}"
            with self.subTest(test=test):
                self.assertRaises(AssertionError, translate, test, typecheck=True, test=True)
