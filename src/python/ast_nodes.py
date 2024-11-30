from dataclasses import dataclass, field

from .lexer import Token
from . import type_defs as types


@dataclass
class Node:
    pos: tuple[int, int] = field(kw_only=True, default=None)


@dataclass
class Declr(Node):
    # used by the type checker
    checked_type: types.Type = field(init=False, default=None)


@dataclass
class Stmt(Node):
    pass


@dataclass
class Expr(Node):
    # used by the type checker
    typ: types.Type = field(kw_only=True, default=None)


@dataclass
class Type(Node):
    pass


@dataclass
class Program(Node):
    declrs: list[Declr]


@dataclass
class Literal(Expr):
    value: Token


@dataclass
class Identifier(Expr):
    value: str


@dataclass
class RangeExpr(Expr):
    start: Expr
    end: Expr


@dataclass
class GroupExpr(Expr):
    value: Expr


@dataclass
class CallExpr(Expr):
    target: Expr
    args: list[Expr]


@dataclass
class IndexExpr(Expr):
    target: Expr
    index: Expr


@dataclass
class SelectorExpr(Expr):
    target: Expr
    name: Identifier


@dataclass
class UnaryExpr(Expr):
    op: Token
    rhs: Expr


@dataclass
class BinaryExpr(Expr):
    op: Token
    lhs: Expr
    rhs: Expr


@dataclass
class TypeName(Type):
    value: Identifier


@dataclass
class ArrayType(Type):
    length: Expr
    elem_type: Type


@dataclass
class Block(Stmt):
    stmt_list: list[Stmt]


@dataclass
class DeclrStmt(Stmt):
    declr: Declr


@dataclass
class ExprStmt(Stmt):
    expr: Expr


@dataclass
class IfStmt(Stmt):
    condition: Expr
    if_block: Block
    else_block: Block


@dataclass
class WhileStmt(Stmt):
    condition: Expr
    block: Block


@dataclass
class ReturnStmt(Stmt):
    value: Expr


@dataclass
class AssignmentStmt(Stmt):
    target: Expr
    value: Expr


@dataclass
class FieldDeclr(Declr):
    name: Identifier
    typ: Type


@dataclass
class FunctionSignature(Type):
    name: Identifier
    return_type: Type | None
    params: list[FieldDeclr]


@dataclass
class FunctionDeclr(Declr):
    signature: FunctionSignature
    block: Block


@dataclass
class StructDeclr(Declr):
    name: Identifier
    fields: list[FieldDeclr]


@dataclass
class InterfaceDeclr(Declr):
    name: Identifier
    methods: list[FunctionSignature]


@dataclass
class ImplDeclr(Declr):
    target: Identifier
    interface: Identifier | None
    methods: list[FunctionDeclr]


@dataclass
class VariableDeclr(Declr):
    name: Identifier
    typ: Type | None
    value: Expr | None


@dataclass
class ConstDeclr(Declr):
    name: Identifier
    typ: Type | None
    value: Expr
