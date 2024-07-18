import sys

from .cmd import exec_file


# TODO: add flags to only run specific modules
assert len(sys.argv) == 2
exec_file(sys.argv[1])
