import logging

from . import ir_nodes as ir
from . import tir_nodes as tir
from . import builtin
from . import type_defs as types


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


class TypeChecker:
    def __init__(self, error_handler=None):
        self.node_map = {}
        # special handling for metatype because of recursion
        # TODO: should metatype really store itself as the type
        meta = tir.Type("meta", checked=builtin.types["meta"])
        #meta.typ = meta
        self.node_map[id(builtin.scope.lookup("meta"))] = meta
        print(self.check(builtin.scope.lookup("meta")))

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
                return types.CompoundType(
                    0,
                    types.TypeFlag.FUNCTION,
                    "fn",
                    param_types + [return_type]  # return type is the final field
                )
            case ir.StructRef():
                fields = [self.get_core_type(v) for v in typ.fields.values()]
                return types.CompoundType(
                    0,
                    types.TypeFlag.STRUCT,
                    "struct",
                    fields,
                )
            case ir.SequenceType():  # TODO
                assert False, "Sequence types are not translated yet"
            case ir.ConstRef():
                if typ.typ == builtin.scope.lookup("meta"):
                    return typ.value.value
            case _:
                assert False, typ

    def update_raw_types(self, target, new):
        if target is None:
            target = new
        if new is None:
            logging.warn(f"Why is the new type None? Given target {target}")
            return target
        if isinstance(target, types.CompoundType):
            # TODO: For functions and structs, should extend to all compound types
            assert len(target.fields) == len(new.fields), \
                "Mismatching number of fields, why is this not already checked?"
            checked_fields = []
            for target_type, new_type in zip(target.fields, new.fields):
                checked_fields.append(self.update_raw_types(target_type, new_type))
            target.fields = checked_fields

            # TODO: fix later
            # case tir.ArrayType() | tir.VectorType():
            #     if isinstance(new, (tir.ArrayType, tir.VectorType)):
            #         assert isinstance(target, type(new)), \
            #             f"Cannot assign object of type {new.checked} " \
            #             f"to ref of type {target.checked}"
            #     new.elem_type = self.update_types(target.elem_type, new.elem_type)
            #     if type(new) is not tir.SequenceType:
            #         target = new
            #     else:
            #         target.elem_type = new.elem_type
            # case tir.SequenceType():
            #     # Update target to the correct IR type, then recurse
            #     if isinstance(target.checked, types.ArrayType):
            #         target = tir.ArrayType(
            #             target.name, self.check(target.elem_type), None, checked=target.checked
            #         )
            #         return self.update_types(target, new)
            #     elif isinstance(target.checked, types.VectorType):
            #         target = tir.VectorType(
            #             target.name, self.check(target.elem_type), checked=target.checked
            #         )
            #         return self.update_types(target, new)
            #     # Or if target is already the correct type, perform standard logic
            #     new.elem_type = self.update_types(target.elem_type, new.elem_type)
            #     if type(new) is not tir.SequenceType:
            #         target = new
            #     else:
            #         target.elem_type = new.elem_type
        elif types.is_basic(target):
            # check equality based on type flags
            assert target == new, f"Mismatching types {target} and {new}"
        else:
            assert False, f"Unexpected type {target}"
        return target

    def update_types(self, target, new):
        # TODO: maybe once the rework is done we don't need this function
        if target is None:
            target = new
        if new is None:
            return target
        match target:
            case tir.FunctionSigRef():
                assert target.param_names == new.param_names, "Mismatching params"
                target.checked = self.update_raw_types(target.checked, new.checked)
                """
                typ = self.update_types(target.return_type, new.return_type)
                new.return_type = target.return_type = typ
                assert target.params.keys() == new.params.keys(), "Mismatching params"
                for pname in target.params:
                    typ = self.update_types(target.params[pname], new.params[pname])
                    new.params[pname] = target.params[pname] = typ
                """
            case tir.StructRef():
                assert target.field_names == new.field_names, "Mismatching fields"
                target.checked = self.update_raw_types(target.checked, new.checked)
            case tir.ArrayType() | tir.VectorType():
                if isinstance(new, (tir.ArrayType, tir.VectorType)):
                    assert isinstance(target, type(new)), \
                        f"Cannot assign object of type {new.checked} " \
                        f"to ref of type {target.checked}"
                new.elem_type = self.update_types(target.elem_type, new.elem_type)
                if type(new) is not tir.SequenceType:
                    target = new
                else:
                    target.elem_type = new.elem_type
            case tir.SequenceType():
                # Update target to the correct IR type, then recurse
                if isinstance(target.checked, types.ArrayType):
                    target = tir.ArrayType(
                        target.name, self.check(target.elem_type), None, checked=target.checked
                    )
                    return self.update_types(target, new)
                elif isinstance(target.checked, types.VectorType):
                    target = tir.VectorType(
                        target.name, self.check(target.elem_type), checked=target.checked
                    )
                    return self.update_types(target, new)
                # Or if target is already the correct type, perform standard logic
                new.elem_type = self.update_types(target.elem_type, new.elem_type)
                if type(new) is not tir.SequenceType:
                    target = new
                else:
                    target.elem_type = new.elem_type
            case tir.Type():
                assert target == new, f"Mismatching types {target} and {new}"
            case _:
                assert False, f"Unexpected type {target}"
        return target

    def check(self, node):
        print(node)
        if (n := self.node_map.get(id(node))):
            return n
        print("not in map")
        match node:
            case ir.Program(block):
                checked_block = self.check(block)
                # TODO: program types
                checked_node = tir.Program(checked_block)
            case ir.Ref():
                checked_node = self.check_ref(node)
            case ir.Instruction():
                checked_node = self.check_instr(node)
            case ir.Object():
                # misc
                checked_node = self.check_object(node)
            case _:
                assert False, f"Unexpected node {node}"
        self.node_map[id(node)] = checked_node
        return checked_node

    def check_ref(self, node):
        checked_type = None
        if node.typ is not None:
            checked_type = self.check(node.typ)
        for value in node.values:
            checked_value = self.check(value)
            checked_type = self.update_types(checked_type, checked_value.typ)
            if isinstance(value.typ, ir.SequenceType):
                value.typ = node.typ
        match node:
            case ir.FunctionRef():
                typ = checked_type
                param_types = []
                for pname, ptype in zip(typ.param_names, typ.checked.fields):
                    values = node.param_values.get(pname, [])
                    for value in values:
                        checked_value = self.check(value)
                        ptype = self.update_types(ptype, checked_value.typ)
                    param_types.append(ptype)

                return_type = typ.checked.fields[-1]
                for value in node.return_values:
                    checked_value = self.check(value)
                    return_type = self.update_raw_types(
                        return_type, checked_value.typ.checked
                    )

                typ.checked.fields = param_types + [return_type]
                checked_node = tir.FunctionRef(node.name, typ=checked_type)

                # TODO: node.params check went here, should it be added back?

                if not node.builtin:
                    block = self.check(node.block)
                    checked_node.block = block
            case ir.FieldRef():
                parent = self.check(node.parent)
                checked_node = None
                if isinstance(parent.typ, tir.StructRef) and node.name in parent.typ.field_names:
                    index = parent.typ.field_names.index(node.name)
                    checked_node = tir.FieldRef(node.name, parent, index=index)
                    raw_type = parent.typ.checked.fields[index]
                    # TODO: this is a hack, find a better way
                    # (we need a consistent way to get a TIR type from a type_defs type)
                    checked_node.typ = tir.Type(raw_type.string, checked=raw_type)
                method = parent.typ.methods.get(node.name)
                if method:
                    assert checked_node is None, f"{node.name} cannot be both a field and a method"
                    for name, value in zip(method.typ.params, node.param_values):
                        values = method.param_values.get(name, [])
                        values.append(value)
                        method.param_values[name] = values
                    for param, value in zip(method.params, node.param_values):
                        self.check(value)
                        param.values.append(value)
                        self.check(param)
                    checked_node = self.check(method)
                assert checked_node is not None, \
                    f"{node.name} is not a field or method of {node.parent.name}"
            case ir.IndexRef():
                checked_parent = self.check(node.parent)
                assert isinstance(checked_parent.typ, tir.SequenceType), \
                    f"{checked_parent.name} cannot be indexed"
                checked_index = self.check(node.index)
                assert types.is_basic(checked_index.typ.checked, types.BasicTypeFlag.INTEGER), \
                    f"Index {checked_index} is not an integer"
                checked_type = checked_parent.typ.elem_type
                checked_node = tir.IndexRef(
                    node.name, checked_parent, checked_index, typ=checked_type
                )
            case ir.ConstRef():
                value = self.check(node.value)
                checked_node = tir.ConstRef(node.name, value)
                checked_node.typ = self.update_types(checked_type, value.typ)
                if checked_node.typ.checked.flags & types.TypeFlag.META:
                    checked_node = tir.Type(node.name, typ=checked_node.typ, checked=value.value)
            case ir.FunctionSigRef():
                param_names = [fname for fname in node.params.keys()]
                raw_type = self.get_core_type(node)
                checked_node = tir.FunctionSigRef(node.name, param_names, checked=raw_type)

                # TODO: is this still necessary?
                # sometimes function sigs have values set (methods)
                for value in node.values:
                    checked_node = self.update_types(checked_node, self.check(value))
            case ir.StructRef():
                field_names = [fname for fname in node.fields.keys()]
                raw_type = self.get_core_type(node)
                checked_node = tir.StructRef(node.name, field_names, checked=raw_type)
            case ir.InterfaceRef():
                checked_methods = {}
                for mname, mtype in node.methods.items():
                    checked_methods[mname] = mtype
                    if mtype is not None:
                        checked_methods[mname] = self.check(mtype)
                checked_node = tir.InterfaceRef(node.name, checked_methods)
            case ir.SequenceType():
                elem_type = node.elem_type
                if isinstance(node, ir.VectorType):
                    checked_node = tir.VectorType(node.name, elem_type)
                elif isinstance(node, ir.ArrayType):
                    checked_node = tir.ArrayType(node.name, elem_type, node.length)
                else:
                    checked_node = tir.SequenceType(node.name, elem_type)
            case ir.Ref():
                checked_node = tir.Ref(node.name, typ=checked_type)
            case _:
                assert False, f"Unexpected ref {node}"
        checked_node.methods = node.methods
        return checked_node

    def check_instr(self, node):
        match node:
            case ir.Declare(ref):
                checked_node = tir.Declare(self.check(ref))
            case ir.DeclareMethods(target, block):
                target = self.check(target)
                print(target)
                if types.TypeFlag.STRUCT in target.checked.flags:
                    assert all(m not in target.checked.fields for m in target.methods)
                checked_methods = {}
                for mname, method in target.methods.items():
                    checked_methods[mname] = self.check(method)
                # TODO: this is a hack
                checked_type = tir.Type(target.checked.string, checked=target.checked)
                checked_type.methods = checked_methods
                checked_node = tir.DeclareMethods(checked_type, self.check(block))
            case ir.Assign(ref, value):
                checked_node = tir.Assign(self.check(ref), self.check(value))
            case ir.Load(ref):
                checked_node = tir.Load(self.check(ref))
                checked_node.typ = checked_node.ref.typ
            case ir.Call(ref, args):
                checked_ref = self.check(ref)
                assert len(args) == len(checked_ref.typ.param_names)
                assert len(args) == len(checked_ref.typ.checked.fields) - 1
                checked_args = []
                for i in range(len(args)):
                    checked_arg = self.check(args[i])
                    checked_args.append(checked_arg)
                    checked_ref.typ.checked.fields[i] = self.update_raw_types(
                        checked_ref.typ.checked.fields[i], checked_arg.typ.checked
                    )
                checked_node = tir.Call(checked_ref, checked_args)
                # TODO: this is a hack
                return_type = checked_ref.typ.checked.fields[-1]
                checked_node.typ = tir.Type(return_type.string, checked=return_type)
            case ir.Return(value):
                checked_node = tir.Return(self.check(value))
            case ir.Branch(block):
                checked_node = tir.Branch(self.check(block))
            case ir.CBranch(condition, t_block, f_block):
                checked_condition = self.check(condition)
                if checked_condition.typ.checked != builtin.types["bool"]:
                    self.error("Branch condition must be a boolean")
                checked_t_block = self.check(t_block)
                checked_f_block = self.check(f_block)
                checked_node = tir.CBranch(checked_condition, checked_t_block, checked_f_block)
            case ir.Binary():
                checked_node = self.check_binary(node)
            case ir.Unary():
                checked_node = self.check_unary(node)
            case _:
                assert False, f"Unexpected instruction {node}"
        return checked_node

    def check_binary(self, node):
        lhs = self.check(node.lhs)
        rhs = self.check(node.rhs)
        checked_node = tir.Binary(node.op, lhs, rhs)

        if lhs.typ != rhs.typ:
            self.error(f"Mismatched types for {lhs} and {rhs}")
        if is_comparison_op(node.op):
            # TODO: ????
            checked_node.typ = self.check(builtin.scope.lookup("bool"))
            return checked_node

        pred = binary_op_preds[node.op]
        if not pred(lhs.typ.checked):
            self.error(f"Unsupported op '{node.op}' on {lhs.typ}")
        elif node.op == '/':
            checked_node.typ = builtin.scope.lookup("float")
        else:
            checked_node.typ = lhs.typ
        return checked_node

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
                checked_instrs = []
                for instr in instrs:
                    checked_instrs.append(self.check(instr))
                # TODO: block types
                checked_node = tir.Block(checked_instrs)
            case ir.Constant():
                typ = self.check(node.typ)
                checked_node = tir.Constant(node.value, typ=typ)
            case ir.Sequence(elements):
                length = len(elements)
                elem_type = None
                checked_elements = []
                for i in range(length):
                    checked_elements.append(self.check(elements[i]))
                    elem_type = self.update_types(elem_type, checked_elements[i].typ)
                if isinstance(node, ir.Vector):
                    checked_type = tir.VectorType(
                        str(node.typ),
                        elem_type,
                        checked=types.VectorType(elem_type.checked)
                    )
                    checked_node = tir.Vector(checked_elements)
                elif isinstance(node, ir.Array):
                    checked_type = tir.ArrayType(
                        str(node.typ),
                        elem_type,
                        length,
                        checked=types.ArrayType(elem_type.checked, length)
                    )
                    checked_node = tir.Array(checked_elements)
                else:
                    checked_type = tir.SequenceType(
                        str(node.typ),
                        elem_type,
                        checked=types.SequenceType(elem_type.checked)
                    )
                    checked_node = tir.Sequence(checked_elements)
                checked_node.typ = checked_type
            case ir.StructLiteral():
                checked_type = self.check(node.typ)
                checked_fields = []
                assert list(node.fields.keys()) == checked_type.field_names
                for i, fval in enumerate(node.fields.values()):
                    checked_val = self.check(fval)
                    checked_fields.append(checked_val)
                    checked_type.checked.fields[i] = self.update_raw_types(
                        checked_type.checked.fields[i], checked_val.typ.checked
                    )
                checked_node = tir.StructLiteral(checked_fields, typ=checked_type)
            case _:
                assert False, f"Unexpected object {node}"
        return checked_node


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
