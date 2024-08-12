import argparse

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

parser.add_argument("filename", help="the file to translate")

cf_g = parser.add_argument_group("control flow diagram")
cf_g.add_argument("--cf-diagram", action="store_true", help="create a control flow diagram")
cf_g.add_argument("--cfpath", help="the path the cf-diagram will be saved under")

args = vars(parser.parse_args())
filename = args.pop("filename")
if args.get("cf_diagram"):
    cfpath = args.pop("cfpath")
if args.get("interpret"):
    cmd.exec_file(filename, cfpath, **args)  # NOTE: idk is this works
elif args.get("compile"):
    cmd.compile_file(filename, cfpath, **args)  # NOTE: idk is this works
else:
    with open(filename) as f:
        src = f.read()
    cmd.translate(src, cfpath, **args)
