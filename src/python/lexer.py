from collections import namedtuple
from enum import Enum, global_enum

TokenType = Enum("TokenType", [
    "INTEGER", "FLOAT", "RATIONAL", "STRING", "BOOL", "IDENTIFIER",
    "INTEGER_TYPE", "FLOAT_TYPE", "RATIONAL_TYPE", "STRING_TYPE", "BOOL_TYPE",
    "EQUALS_EQUALS", "BANG_EQUALS",
    "LESS_THAN", "GREATER_THAN", "LESS_EQUALS", "GREATER_EQUALS",
    "EQUALS", "STAR", "SLASH", "PLUS", "MINUS", "BANG",
    "SEMICOLON", "COLON", "COMMA", "DOT",
    "LEFT_BRACKET", "RIGHT_BRACKET",
    "LEFT_CURLY", "RIGHT_CURLY", "LEFT_SQUARE", "RIGHT_SQUARE",
    "IF", "ELSE", "WHILE", "RETURN",
    "VAR", "FUNC", "STRUCT", "INTERFACE",
])
Token = namedtuple("Token", ["typ", "lexeme"])

# export members to global namespace
# when importing the types use TokenType
global_enum(TokenType)

KEYWORDS = {
    "true": BOOL,
    "false": BOOL,
    "if": IF,
    "else": ELSE,
    "while": WHILE,
    "return": RETURN,
    "var": VAR,
    "fn": FUNC,
    "struct": STRUCT,
    "interface": INTERFACE,
}

DIGRAPHS = {
    "==": EQUALS_EQUALS,
    "!=": BANG_EQUALS,
    "<=": LESS_EQUALS,
    ">=": GREATER_EQUALS,
}
MONOGRAPHS = {
    "<": LESS_THAN,
    ">": GREATER_THAN,
    "=": EQUALS,
    "*": STAR,
    "/": SLASH,
    "+": PLUS,
    "-": MINUS,
    "!": BANG,
    ";": SEMICOLON,
    ":": COLON,
    ",": COMMA,
    ".": DOT,
    "(": LEFT_BRACKET,
    ")": RIGHT_BRACKET,
    "{": LEFT_CURLY,
    "}": RIGHT_CURLY,
    "[": LEFT_SQUARE,
    "]": RIGHT_SQUARE,
}

def get(src, index, length=1):
    if index + length <= len(src):
        return src[index:index+length]
    else:
        return ""

def tokenise(src):
    cur = 0
    tokens = []
    while cur < len(src):
        char = src[cur]
        if char.isspace():
            cur += 1
            continue
        elif char.isalpha() or char == '_':
            # identifier or keyword (including bool or type)
            i = 0
            while (c := get(src, cur + i)).isalnum() or c == '_':
                i += 1
            lexeme = src[cur:cur + i]
            typ = KEYWORDS.get(lexeme) or IDENTIFIER
        elif char.isnumeric():
            # int or float
            i = 0
            typ = INTEGER
            while get(src, cur + i).isnumeric():
                i += 1
                if typ == INTEGER:
                    if get(src, cur + i) == '.' and \
                       get(src, cur + i + 1).isnumeric():
                        typ = FLOAT
                        i += 1
                    elif get(src, cur + i, 2) == '//' and \
                         get(src, cur + i + 2).isnumeric():
                        typ = RATIONAL
                        i += 2
            lexeme = src[cur:cur + i]
        elif char == '"':
            # string
            i = 1
            while get(src, cur + i) != '"':
                i += 1
            i += 1
            lexeme = src[cur:cur + i]
            typ = STRING
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
            assert False, "Tokenisation: Syntax Error"
        tokens.append(Token(typ, lexeme))
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
