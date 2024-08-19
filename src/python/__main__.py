import argparse
import logging

from . import cmd


parser = argparse.ArgumentParser(
    prog="starling",
    description="Translate a Starling source file",
)

t_mode_g = parser.add_argument_group("translation mode")
t_mode = t_mode_g.add_mutually_exclusive_group(required=True)
t_mode.add_argument("-i", "--interpret", action="store_true")
t_mode.add_argument("-c", "--compile", action="store_true")
t_mode.add_argument("--tokenise", action="store_true")
t_mode.add_argument("--parse", action="store_true")
t_mode.add_argument("--make-ir", action="store_true")
t_mode.add_argument("--typecheck", action="store_true")

cf_g = parser.add_argument_group("control flow diagram")
cf_g.add_argument("--cf-show", action="store_true", help="display a control flow diagram")
cf_g.add_argument("--cf-path", help="save a cf-diagram at the given path")

parser.add_argument("-v", "--verbosity", action="count")

parser.add_argument("--test", action="store_true", help="causes the IRPrinter to enter test mode")

parser.add_argument("filename", help="the file to translate")

logging_levels = (logging.ERROR, logging.WARNING, logging.INFO, logging.DEBUG)

args = vars(parser.parse_args())
filename = args.pop("filename")
verbosity = args.pop("verbosity") or 0
logging_level = logging_levels[verbosity]
logging.basicConfig(format="%(levelname)s: %(message)s")
logging.getLogger().setLevel(logging_level)

if args.get("interpret"):
    cmd.exec_file(filename, **args)
elif args.get("compile"):
    cmd.compile_file(filename, **args)
else:
    with open(filename) as f:
        src = f.read()
    print(cmd.translate(src, **args))
