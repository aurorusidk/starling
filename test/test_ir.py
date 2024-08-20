import unittest
from src.python.cmd import translate


class TestIR(unittest.TestCase):
    def test_globals(self):
        # TODO: add interfaces once fully implemented
        tests = {
                """
                fn main() {
                }
                """:
                "\n1:\n DEFINE main() 2\n2:\n [empty]",
                """
                fn test() {
                }
                fn main() {
                }
                """: "\n1:\n DEFINE test() 2\n DEFINE main() 3\n2:\n [empty]\n3:\n [empty]",
                """
                struct test {
                    a int;
                }
                """: "\n1:\n DECLARE test{a}",
                }

        for test, expected in tests.items():
            self.assertEqual(translate(test, make_ir=True, test=True), expected)

    def test_valid_ref(self):
        tests = {
                """
                struct test {
                    a int;
                }

                fn main() {
                    var b = test;
                    var c = b.a;
                }
                """:
                """\n1:\n DECLARE test{a}\n DEFINE main() 2\n2:\n DECLARE b
 ASSIGN b <- LOAD(test{a})\n DECLARE c\n ASSIGN c <- LOAD(b.a)""",
                """
                fn test() {
                }

                fn main() {
                    test();
                }
                """:
                "\n1:\n DEFINE test() 2\n DEFINE main() 3\n2:\n [empty]\n3:\n CALL test() ()"
                }

        for test, expected in tests.items():
            self.assertEqual(translate(test, make_ir=True, test=True), expected)

    def test_valid_instr(self):
        # CALL instruction tested in test_valid_ref
        tests = {
                "var a;":
                "\n1:\n DEFINE main() 2\n2:\n DECLARE a",
                "var a; a = 5;":
                "\n1:\n DEFINE main() 2\n2:\n DECLARE a\n ASSIGN a <- 5 [int]",
                "var a; var b = a;":
                "\n1:\n DEFINE main() 2\n2:\n DECLARE a\n DECLARE b\n ASSIGN b <- LOAD(a)",
                "return 0;":
                "\n1:\n DEFINE main() 2\n2:\n RETURN 0 [int]",
                "var a; while a < 2 {a = a + 1;}":
                """\n1:\n DEFINE main() 2\n2:\n DECLARE a\n BRANCH 3\n3:
 CBRANCH (LOAD(a) < 2 [int]) 4 5\n4:\n ASSIGN a <- (LOAD(a) + 1 [int])\n BRANCH 3\n5:\n [empty]""",
                "if true return 0;":
                """\n1:\n DEFINE main() 2\n2:\n CBRANCH True [bool] 3 4\n3:\n RETURN 0 [int]\n4:
 [empty]""",
                "fn test() {}":
                "\n1:\n DEFINE main() 2\n3:\n [empty]\n2:\n DEFINE test() 3",
                "var a = 5; a = a + 5;":
                """\n1:\n DEFINE main() 2\n2:\n DECLARE a\n ASSIGN a <- 5 [int]
 ASSIGN a <- (LOAD(a) + 5 [int])"""
                }

        for test_contents, expected in tests.items():
            test = "fn main() {" + test_contents + "}"
            self.assertEqual(translate(test, make_ir=True, test=True), expected)

    def test_invalid(self):
        # TODO: add more invalid testing where reasonable
        tests = [
                "a = 5;"
                ]

        for test_contents in tests:
            test = "fn main() {" + test_contents + "}"
            self.assertRaises(AssertionError, translate, test, make_ir=True, test=True)
