from collections import namedtuple
from dataclasses import dataclass
from enum import Enum


TokenType = Enum("TokenType", [
    "INTEGER", "FLOAT", "RATIONAL", "STRING", "BOOLEAN", "IDENTIFIER",
    "OPTIONAL", "NIL",
    "EQUALS_EQUALS", "BANG_EQUALS",
    "LESS_THAN", "GREATER_THAN", "LESS_EQUALS", "GREATER_EQUALS",
    "EQUALS", "STAR", "SLASH", "PLUS", "MINUS", "BANG",
    "SEMICOLON", "COLON", "COMMA", "DOT",
    "LEFT_BRACKET", "RIGHT_BRACKET",
    "LEFT_CURLY", "RIGHT_CURLY", "LEFT_SQUARE", "RIGHT_SQUARE",
    "IF", "ELSE", "WHILE", "RETURN",
    "VAR", "FUNC", "STRUCT", "INTERFACE", "IMPL",
])
Token = namedtuple("Token", ["typ", "lexeme", "pos"])


@dataclass
class Pos:
    line: int
    col: int

    def __iadd__(self, other):
        return Pos(self.line, self.col + other)


T = TokenType


KEYWORDS = {
    "true": T.BOOLEAN,
    "false": T.BOOLEAN,
    "Optional": T.OPTIONAL,
    "nil": T.NIL,
    "if": T.IF,
    "else": T.ELSE,
    "while": T.WHILE,
    "return": T.RETURN,
    "var": T.VAR,
    "fn": T.FUNC,
    "struct": T.STRUCT,
    "interface": T.INTERFACE,
    "impl": T.IMPL,
}

DIGRAPHS = {
    "==": T.EQUALS_EQUALS,
    "!=": T.BANG_EQUALS,
    "<=": T.LESS_EQUALS,
    ">=": T.GREATER_EQUALS,
}
MONOGRAPHS = {
    "<": T.LESS_THAN,
    ">": T.GREATER_THAN,
    "=": T.EQUALS,
    "*": T.STAR,
    "/": T.SLASH,
    "+": T.PLUS,
    "-": T.MINUS,
    "!": T.BANG,
    ";": T.SEMICOLON,
    ":": T.COLON,
    ",": T.COMMA,
    ".": T.DOT,
    "(": T.LEFT_BRACKET,
    ")": T.RIGHT_BRACKET,
    "{": T.LEFT_CURLY,
    "}": T.RIGHT_CURLY,
    "[": T.LEFT_SQUARE,
    "]": T.RIGHT_SQUARE,
}

SEMICOLON_INSERT = [
    T.INTEGER, T.FLOAT, T.RATIONAL, T.STRING, T.BOOLEAN, T.IDENTIFIER,
    T.NIL,
    T.RIGHT_BRACKET, T.RIGHT_SQUARE,
    T.RETURN,
]


def get(src, index, length=1):
    if index + length <= len(src):
        return src[index:index+length]
    else:
        return ""


def tokenise(src, error_handler=None):
    cur = 0
    pos = Pos(1, 1)
    tokens = []
    while cur < len(src):
        cur_pos = pos
        lexeme = None
        typ = None
        char = src[cur]
        if char == '\n':
            pos = Pos(pos.line + 1, 1)
            # automatic semicolon insertion
            if tokens and tokens[-1].typ in SEMICOLON_INSERT:
                lexeme = ';'
                typ = T.SEMICOLON
            else:
                cur += 1
                continue
        elif char.isspace():
            pos += 1
            cur += 1
            continue
        elif char.isalpha() or char == '_':
            # identifier or keyword (including bool or type)
            i = 0
            while (c := get(src, cur + i)).isalnum() or c == '_':
                i += 1
            lexeme = src[cur:cur + i]
            typ = KEYWORDS.get(lexeme) or T.IDENTIFIER
        elif char.isnumeric():
            # int or float
            i = 0
            typ = T.INTEGER
            while get(src, cur + i).isnumeric():
                i += 1
                if typ == T.INTEGER:
                    if (
                        get(src, cur + i) == '.' and
                        get(src, cur + i + 1).isnumeric()
                    ):
                        typ = T.FLOAT
                        i += 1
                    elif (
                        get(src, cur + i, 2) == '//' and
                        get(src, cur + i + 2).isnumeric()
                    ):
                        typ = T.RATIONAL
                        i += 2
            lexeme = src[cur:cur + i]
        elif char == '"':
            # string
            i = 1
            while get(src, cur + i) != '"':
                i += 1
            i += 1
            lexeme = src[cur:cur + i]
            typ = T.STRING
        else:
            # all the easy tokens
            for monograph, token in MONOGRAPHS.items():
                if char == monograph:
                    lexeme = monograph
                    typ = token
                    break
            for digraph, token in DIGRAPHS.items():
                if char + get(src, cur + 1) == digraph:
                    lexeme = digraph
                    typ = token
                    break

        if not lexeme:
            # syntax error (unexpected char)
            msg = f"Syntax error: unexpected character '{char}'"
            if error_handler is None:
                assert False, msg
            else:
                error_handler(msg)
        tokens.append(Token(typ, lexeme, cur_pos))
        pos += len(lexeme)
        cur += len(lexeme)
    return tokens


if __name__ == "__main__":
    import sys
    if len(sys.argv) == 2:
        src_file = sys.argv[1]
    else:
        src_file = "input.txt"
    with open(src_file) as f:
        src = f.read()
    tokens = tokenise(src)
    print(tokens)
