from .type_defs import BasicType, BasicTypeKind, BasicTypeFlag
from . import type_defs
from . import ir_nodes as ir
from .scope import Scope


types = {
    "int": BasicType(BasicTypeKind.INT, BasicTypeFlag.INTEGER, "int"),
    "float": BasicType(BasicTypeKind.FLOAT, BasicTypeFlag.FLOAT, "float"),
    "frac": BasicType(BasicTypeKind.FRAC, BasicTypeFlag.RATIONAL, "frac"),
    "str": BasicType(BasicTypeKind.STR, BasicTypeFlag.STRING, "str"),
    "bool": BasicType(BasicTypeKind.BOOL, BasicTypeFlag.BOOLEAN, "bool"),
}


def get_ir_type(type_name):
    typ = types[type_name]
    return ir.Type(
        typ._string,
        typ,
        checked=typ,
        progress=type_defs.progress.COMPLETED
    )


# TODO: builtin name definitions (vars and funcs)
names = {
    "range_constructor@builtin": ir.FunctionRef(
        "range_constructor@builtin",
        typ=ir.FunctionSigRef(
            "range_constructor@builtin",
            type_defs.FunctionType(
                type_defs.ArrayType(types["int"], None),
                [types["int"], types["int"]]
            ),
            {"start": get_ir_type("int"), "end": get_ir_type("int")},
            ir.SequenceType(
                name="arr[int,None]",
                elem_type=get_ir_type("int"),
                hint=type_defs.ArrayType(types["int"], None),
                checked=type_defs.ArrayType(types["int"], None),
            )
        ),
        params=[
            ir.Ref("start", typ=get_ir_type("int")),
            ir.Ref("end", typ=get_ir_type("int")),
        ],
        builtin=True
    ),
}

scope = Scope(None)
for name, value in types.items():
    ref = ir.Type(name, value, checked=value)
    scope.declare(name, ref)
for name, value in names.items():
    scope.declare(name, value)
