from dataclasses import dataclass

from lexer import Token


@dataclass
class Node:
    pos: tuple[int, int]


@dataclass
class Declr(Node):
    pass


@dataclass
class Stmt(Node):
    pass


@dataclass
class Expr(Node):
    pass


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
    elem_typ: Type


@dataclass
class Block(Stmt):
    stmt_list: list[Stmt]


@dataclass
class DeclrStmt(Stmt):
    declr: Declr


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
class Parameter(Node):
    name: Identifier
    typ: Type | None


@dataclass
class FunctionDeclr(Declr):
    name: Identifier
    return_type: Type | None
    params: list[Parameter]
    block: Block


@dataclass
class VariableDeclr(Declr):
    name: Identifier
    typ: Type | None
    value: Expr


