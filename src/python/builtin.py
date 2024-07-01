from type_defs import BasicType, BasicTypeKind, BasicTypeFlag


types = {
        "int": BasicType(BasicTypeKind.INT, BasicTypeFlag.INTEGER, "int"),
        "float": BasicType(BasicTypeKind.FLOAT, BasicTypeFlag.FLOAT, "float"),
        "frac": BasicType(BasicTypeKind.FRAC, BasicTypeFlag.RATIONAL, "frac"),
        "str": BasicType(BasicTypeKind.STR, BasicTypeFlag.STRING, "str"),
        "bool": BasicType(BasicTypeKind.BOOL, BasicTypeFlag.BOOLEAN, "bool"),
}

# TODO: builtin name definitions (vars and funcs)

