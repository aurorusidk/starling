import logging

from . import ir_nodes as ir
from . import builtin
from . import type_defs as types


progress = types.progress

unary_op_preds = {
    '-': types.is_numeric,
    '!': types.is_bool,
}

binary_op_preds = {
    '+': lambda t: types.is_numeric(t) or types.is_string(t),
    '-': types.is_numeric,
    '*': types.is_numeric,
    '/': types.is_numeric,
}


def is_comparison_op(op):
    return op in (
        '>', '<', '>=', '<=', '==', '!=',
    )


class DeferChecking(Exception):
    pass


class TypeChecker:
    def __init__(self, error_handler=None):
        # used to infer return types
        self.function = None
        self.error_handler = error_handler
        self.deferred = []

    def error(self, msg):
        if self.error_handler is None:
            assert False, msg

        self.error_handler(msg)

    def get_core_type(self, typ):
        match typ:
            case None:
                return
            case ir.FunctionSigRef():
                param_types = [self.get_core_type(p) for p in typ.params.values()]
                return_type = self.get_core_type(typ.return_type)
                return types.FunctionType(return_type, param_types)
            case ir.StructRef():
                fields = {k: self.get_core_type(v) for k, v in typ.fields.items()}
                return types.StructType(fields)
            case ir.Type():
                return typ.checked
            case _:
                assert False

    def update_types(self, target, new):
        if target is None:
            target = new
        if new is None:
            return target
        match target:
            case ir.FunctionSigRef():
                typ = self.update_types(target.return_type, new.return_type)
                new.return_type = target.return_type = typ
                assert target.params.keys() == new.params.keys(), "Mismatching params"
                for pname in target.params:
                    typ = self.update_types(target.params[pname], new.params[pname])
                    new.params[pname] = target.params[pname] = typ
            case ir.StructRef():
                assert target.fields.keys() == new.fields.keys(), "Mismatching fields"
                for fname in target.fields:
                    typ = self.update_types(target.fields[fname], new.fields[fname])
                    new.fields[fname] = target.fields[fname] = typ
            case ir.SequenceType():
                target.elem_type = self.update_types(target.elem_type, new.elem_type)
                target.hint.elem_type = target.elem_type.checked
                self.check_type(target)
            case ir.Type():
                assert target == new, f"Mismatching types {target} and {new}"
            case _:
                assert False, f"Unexpected type {target}"
        target.checked = self.get_core_type(target)
        return target

    def check(self, node):
        if node.progress in (progress.UPDATING, progress.COMPLETED):
            return
        node.progress = progress.UPDATING
        try:
            match node:
                case ir.Program(block):
                    self.check(block)
                    already_deferred = []
                    while self.deferred:
                        logging.debug(self.deferred)
                        node = self.deferred.pop(0)
                        if node in already_deferred:
                            continue
                        already_deferred.append(node)
                        node.progress = progress.EMPTY
                        try:
                            self.check(node)
                        except DeferChecking:
                            pass
                    node.progress = progress.COMPLETED
                case ir.Type():
                    self.check_type(node)
                case ir.Ref():
                    self.check_ref(node)
                case ir.Instruction():
                    self.check_instr(node)
                case ir.Object():
                    # misc
                    self.check_object(node)
                case _:
                    assert False, f"Unexpected node {node}"
        except DeferChecking:
            self.deferred.append(node)
            if node.is_expr:
                logging.info("raise DeferChecking to propagate")
                raise DeferChecking("Propagating expr defer")
        else:
            if node.is_expr and node.typ is None:
                node.progress = progress.EMPTY
            if node.progress != progress.COMPLETED:
                node.progress = progress.EMPTY
                logging.info(f"raise DeferChecking for incomplete type for {type(node)}")
                raise DeferChecking(f"Incomplete type checking for {type(node)} node")

    def check_type(self, node):
        if node.checked is None:
            node.checked = node.hint
        match node:
            case ir.FunctionSigRef():
                if node.return_type is not None:
                    self.check_type(node.return_type)
                for param in node.params.values():
                    if param is not None:
                        self.check_type(param)
            case ir.StructRef():
                for field in node.fields.values():
                    if field is not None:
                        self.check_type(field)
            case ir.InterfaceRef():
                for method in node.methods.values():
                    if method is not None:
                        self.check_type(method)
        node.checked = self.get_core_type(node)
        node.progress = progress.COMPLETED

    def check_ref(self, node):
        if node.typ is not None:
            self.check_type(node.typ)
        for value in node.values:
            self.check(value)
            node.typ = self.update_types(node.typ, value.typ)
            if isinstance(value.typ, ir.SequenceType):
                value.typ = node.typ
        match node:
            case ir.FunctionRef():
                typ = node.typ
                for value in node.return_values:
                    self.check(value)
                    typ.return_type = self.update_types(typ.return_type, value.typ)

                for pname, ptype in typ.params.items():
                    values = node.param_values.get(pname, [])
                    for value in values:
                        self.check(value)
                        typ.params[pname] = self.update_types(ptype, value.typ)
                for param in node.params:
                    self.check(param)
                if not node.builtin:
                    self.check(node.block)
            case ir.FieldRef():
                self.check(node.parent)
                field = None
                if isinstance(node.parent.typ, ir.StructRef):
                    field = node.parent.typ.fields.get(node.name)
                method = node.parent.typ.methods.get(node.name)
                if method:
                    node.method = method
                    for name, value in zip(method.typ.params, node.param_values):
                        values = method.param_values.get(name, [])
                        values.append(value)
                        method.param_values[name] = values
                    for param, value in zip(method.params, node.param_values):
                        self.check(value)
                        param.values.append(value)
                        self.check(param)
                    self.check(method)
                    method = method.typ
                value = field or method
                assert value, f"{node.name} is not a field or method of {node.parent.name}"
                assert not (field and method)
                node.typ = value
            case ir.IndexRef():
                self.check(node.parent)
                assert isinstance(node.parent.typ, ir.SequenceType), \
                    f"{node.parent.name} cannot be indexed"
                self.check(node.index)
                assert types.is_basic(node.index.typ.checked, types.BasicTypeFlag.INTEGER), \
                    f"Index {node.index} is not an integer"
                node.typ = node.parent.typ.elem_type
            case ir.Ref():
                pass
            case _:
                assert False, f"Unexpected ref {node}"

        if node.typ is not None and node.typ.checked is not None:
            node.progress = progress.COMPLETED
        else:
            node.progress = progress.EMPTY
            logging.info("raise DeferChecking for incomplete type")
            raise DeferChecking

    def check_instr(self, node):
        match node:
            case ir.Declare(ref):
                self.check(ref)
            case ir.DeclareMethods(typ, block):
                if isinstance(typ, types.StructType):
                    assert all(m not in typ.fields for m in typ.methods)
                for method in typ.methods.values():
                    self.check(method)
                self.check(block)
            case ir.Assign(ref, value):
                self.check(ref)
                self.check(value)
            case ir.Load(ref):
                self.check(ref)
                node.typ = ref.typ
            case ir.Call(ref, args):
                self.check(ref)
                assert len(args) == len(ref.typ.params)
                for pname, arg in zip(ref.typ.params, args):
                    self.check(arg)
                    ref.typ.params[pname] = self.update_types(ref.typ.params[pname], arg.typ)
                node.typ = ref.typ.return_type
            case ir.Return(value):
                self.check(value)
            case ir.Branch(block):
                self.check(block)
            case ir.CBranch(condition, t_block, f_block):
                self.check(condition)
                if condition.typ != builtin.scope.lookup("bool"):
                    self.error("Branch condition must be a boolean")
                self.check(t_block)
                self.check(f_block)
            case ir.Binary():
                self.check_binary(node)
            case ir.Unary():
                self.check_unary(node)
            case _:
                assert False, f"Unexpected instruction {node}"
        node.progress = progress.COMPLETED

    def check_binary(self, node):
        self.check(node.lhs)
        self.check(node.rhs)

        if node.lhs.typ != node.rhs.typ:
            self.error(f"Mismatched types for {node.lhs} and {node.rhs}")
        if is_comparison_op(node.op):
            node.typ = builtin.scope.lookup("bool")
            return

        pred = binary_op_preds[node.op]
        if not pred(node.lhs.typ.checked):
            self.error(f"Unsupported op '{node.op}' on {node.lhs.typ}")
        elif node.op == '/':
            node.typ = builtin.scope.lookup("float")
        else:
            node.typ = node.lhs.typ

    def check_unary(self, node):
        self.check(node.rhs)

        pred = unary_op_preds[node.op]
        if not pred(node.rhs.typ.checked):
            self.error(f"Unsupported op {node.op} on {node.rhs.typ}")
        else:
            node.typ = node.rhs.typ

    def check_object(self, node):
        match node:
            case ir.Block(instrs):
                for instr in instrs:
                    self.check(instr)
            case ir.Constant():
                pass
            case ir.Sequence(elements):
                length = len(elements)
                elem_type = None
                for i in range(length):
                    self.check(elements[i])
                    elem_type = self.update_types(elem_type, elements[i].typ)
                if node.typ is None:
                    if isinstance(node, ir.Vector):
                        node.typ = ir.SequenceType(
                            str(node.typ),
                            types.VectorType(elem_type.checked),
                            elem_type
                        )
                    elif isinstance(node, ir.Array):
                        node.typ = ir.SequenceType(
                            str(node.typ),
                            types.ArrayType(elem_type.checked, length),
                            elem_type
                        )
                    else:
                        node.typ = ir.SequenceType(
                            str(node.typ),
                            types.SequenceType(elem_type.checked),
                            elem_type
                        )
                self.check_type(node.typ)
            case ir.StructLiteral():
                self.check_type(node.typ)
                for fname, fval in node.fields.items():
                    self.check(fval)
                    assert fval.typ == node.typ.fields[fname]
            case _:
                assert False, f"Unexpected object {node}"
        node.progress = progress.COMPLETED


if __name__ == "__main__":
    from . import lexer
    from . import parser
    from . import ir as noder

    logging.basicConfig(format="%(levelname)s: %(message)s")
    logging.getLogger().setLevel(logging.DEBUG)
    with open("input.txt") as f:
        src = f.read()
    toks = lexer.tokenise(src)
    tree = parser.parse(toks)
    iir = noder.IRNoder().make(tree)
    print(iir)
    print(ir.IRPrinter().to_string(iir))
    tc = TypeChecker(iir)
    tc.check(iir)
    print(iir)
    print(ir.IRPrinter().to_string(iir))
