import argparse

from .cmd import exec_file, compile_file


parser = argparse.ArgumentParser(
    prog="starling",
    description="Translate a Starling source file",
)

t_mode_g = parser.add_argument_group("translation mode")
t_mode = t_mode_g.add_mutually_exclusive_group(required=True)
t_mode.add_argument("-i", "--interpret", action="store_true")
t_mode.add_argument("-c", "--compile", action="store_true")

parser.add_argument("filename", help="the file to translate")

args = parser.parse_args()
if args.interpret:
    exec_file(args.filename)
elif args.compile:
    compile_file(args.filename)
else:
    assert False, "Unreachable"
