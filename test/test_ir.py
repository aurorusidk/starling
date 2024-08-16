import unittest
from src.python.cmd import translate


class TestIR(unittest.TestCase):
    def test_globals(self):
        # TODO: add interfaces once fully implemented
        tests = {
            "fn main() {}": (
                "1:\n"
                " DECLARE main() #2\n"
                "2:\n"
                " [empty]"
            ),
            """
            fn test() {}
            fn main() {}
            """: (
                "1:\n"
                " DECLARE test() #2\n"
                " DECLARE main() #3\n"
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
                " DECLARE test{a}"
            ),
        }

        for test, expected in tests.items():
            self.assertEqual(str(translate(test, make_ir=True, test=True)), expected)

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
                " DECLARE test{a}\n"
                " DECLARE main() #2\n"
                "2:\n"
                " DECLARE b\n"
                " DECLARE c\n"
                " ASSIGN c <- LOAD(b.a)"
            ),
            """
            fn test() {
            }

            fn main() {
                test();
            }
            """: (
                "1:\n"
                " DECLARE test() #2\n"
                " DECLARE main() #3\n"
                "2:\n"
                " [empty]\n"
                "3:\n"
                " CALL test() #2 ()"
            ),
        }

        for test, expected in tests.items():
            self.assertEqual(str(translate(test, make_ir=True, test=True)), expected)

    def test_valid_instr(self):
        # CALL instruction tested in test_valid_ref
        tests = {
            "var a;": (
                "1:\n"
                " DECLARE main() #2\n"
                "2:\n"
                " DECLARE a"
            ),
            "var a; a = 5;": (
                "1:\n"
                " DECLARE main() #2\n"
                "2:\n"
                " DECLARE a\n"
                " ASSIGN a <- 5 [int]"
            ),
            "var a; var b = a;": (
                "1:\n"
                " DECLARE main() #2\n"
                "2:\n"
                " DECLARE a\n"
                " DECLARE b\n"
                " ASSIGN b <- LOAD(a)"
            ),
            "return 0;": (
                "1:\n"
                " DECLARE main() #2\n"
                "2:\n"
                " RETURN 0 [int]"
            ),
            "var a; while a < 2 {a = a + 1;}": (
                "1:\n"
                " DECLARE main() #2\n"
                "2:\n"
                " DECLARE a\n"
                " BRANCH #3\n"
                "3:\n"
                " CBRANCH (LOAD(a) < 2 [int]) #4 #5\n"
                "4:\n"
                " ASSIGN a <- (LOAD(a) + 1 [int])\n"
                " BRANCH #3\n"
                "5:\n"
                " [empty]"
            ),
            "if true return 0;": (
                "1:\n"
                " DECLARE main() #2\n"
                "2:\n"
                " CBRANCH True [bool] #3 #4\n"
                "3:\n"
                " RETURN 0 [int]\n"
                "4:\n"
                " [empty]"
            ),
            "fn test() {}": (
                "1:\n"
                " DECLARE main() #2\n"
                "2:\n"
                " DECLARE test() #3\n"
                "3:\n"
                " [empty]"
            ),
            "var a = 5; a = a + 5;": (
                "1:\n"
                " DECLARE main() #2\n"
                "2:\n"
                " DECLARE a\n"
                " ASSIGN a <- 5 [int]\n"
                " ASSIGN a <- (LOAD(a) + 5 [int])"
            ),
        }

        for test_contents, expected in tests.items():
            test = "fn main() {" + test_contents + "}"
            self.assertEqual(str(translate(test, make_ir=True, test=True)), expected)

    def test_invalid(self):
        # TODO: add more invalid testing where reasonable
        tests = [
                "a = 5;"
                ]

        for test_contents in tests:
            test = "fn main() {" + test_contents + "}"
            self.assertRaises(AssertionError, translate, test, make_ir=True, test=True)
