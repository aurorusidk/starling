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
            self.assertEqual(str(translate(test, make_ir=True, test=True)), expected)

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
            self.assertEqual(str(translate(test, make_ir=True, test=True)), expected)

    def test_invalid_ref(self):
        tests = {}

    def test_valid_instr(self):
        tests = {}

    def test_invalid_instr(self):
        tests = {}

    def test_valid_object(self):
        tests = {}

    def test_invalid_object(self):
        tests = {}
