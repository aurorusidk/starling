const std = @import("std");
const print = std.debug.print;

pub const Token = struct {
    type: TokenType,
    pos: Pos,

    pub const Pos = struct {
        start: usize,
        end: usize,
    };
    pub const TokenType = enum {
        integer,
        float,
        rational,
        string,
        boolean,
        identifier,
        equals_equals,
        bang_equals,
        less_than,
        greater_than,
        less_equals,
        greater_equals,
        equals,
        star,
        slash,
        plus,
        minus,
        bang,
        semicolon,
        colon,
        comma,
        dot,
        left_bracket,
        right_bracket,
        left_curly,
        right_curly,
        left_square,
        right_square,
        kw_if,
        kw_else,
        kw_while,
        kw_return,
        kw_var,
        kw_func,
        kw_struct,
        kw_interface,
        kw_impl,

        pub fn lexeme(tok_type: TokenType) ?[]const u8 {
            return switch (tok_type) {
                .integer, .float, .rational, .string, .boolean, .identifier => null,
                .equals_equals => "==",
                .bang_equals => "!=",
                .less_than => "<",
                .greater_than => ">",
                .less_equals => "<=",
                .greater_equals => ">=",
                .equals => "=",
                .star => "*",
                .slash => "/",
                .plus => "+",
                .minus => "-",
                .bang => "!",
                .semicolon => ";",
                .colon => ":",
                .comma => ",",
                .dot => ".",
                .left_bracket => "(",
                .right_bracket => ")",
                .left_curly => "{",
                .right_curly => "}",
                .left_square => "[",
                .right_square => "]",
                .kw_if => "if",
                .kw_else => "else",
                .kw_while => "while",
                .kw_return => "return",
                .kw_var => "var",
                .kw_func => "fn",
                .kw_struct => "struct",
                .kw_interface => "interface",
                .kw_impl => "impl",
            };
        }
    };
    pub const keywords = std.StaticStringMap(TokenType).initComptime(.{
        .{ "true", .boolean },
        .{ "false", .boolean },
        .{ "if", .kw_if },
        .{ "else", .kw_else },
        .{ "while", .kw_while },
        .{ "return", .kw_return },
        .{ "var", .kw_var },
        .{ "fn", .kw_func },
        .{ "struct", .kw_struct },
        .{ "interface", .kw_interface },
        .{ "impl", .kw_impl },
    });
    pub const digraphs = std.StaticStringMap(TokenType).initComptime(.{
        .{ "==", .equals_equals },
        .{ "!=", .bang_equals },
        .{ "<=", .less_equals },
        .{ ">=", .greater_equals },
    });
    pub const monographs = std.StaticStringMap(TokenType).initComptime(.{
        .{ "<", .less_than },
        .{ ">", .greater_than },
        .{ "=", .equals },
        .{ "*", .star },
        .{ "/", .slash },
        .{ "+", .plus },
        .{ "-", .minus },
        .{ "!", .bang },
        .{ ";", .semicolon },
        .{ ":", .colon },
        .{ ",", .comma },
        .{ ".", .dot },
        .{ "(", .left_bracket },
        .{ ")", .right_bracket },
        .{ "{", .left_curly },
        .{ "}", .right_curly },
        .{ "[", .left_square },
        .{ "]", .right_square },
    });
    pub fn semicolon_insert(tok: Token) bool {
        return switch (tok.type) {
            .integer,
            .float,
            .rational,
            .string,
            .boolean,
            .identifier,
            .right_bracket,
            .right_square,
            .kw_return,
            => true,
            else => false,
        };
    }
};

fn tokenise(allocator: std.mem.Allocator, src: []const u8) []Token {
    var cur: usize = 0;
    var tokens = std.ArrayList(Token).init(allocator);
    while (cur < src.len) {
        var end: usize = 1;
        var typ: Token.TokenType = undefined;
        switch (src[cur]) {
            '\n' => {
                if (tokens.items.len > 0 and tokens.items[tokens.items.len - 2].semicolon_insert()) {
                    typ = .semicolon;
                    end = 0;
                } else {
                    cur += 1;
                    continue;
                }
            },
            ' ', '\t', '\r' => {
                cur += 1;
                continue;
            },
            'a'...'z', 'A'...'Z', '_' => {
                var i: usize = 0;
                while (cur + i < src.len) {
                    switch (src[cur + i]) {
                        'a'...'z', 'A'...'Z', '_' => i += 1,
                        else => {
                            break;
                        },
                    }
                }
                //print("{d}\n", .{}
                typ = Token.keywords.get(src[cur .. cur + i]) orelse .identifier;
                end = i;
            },
            '0'...'9' => {
                var i: usize = 0;
                typ = .integer;
                while (cur + i < src.len) {
                    i += 1;
                    if (typ == .integer) {
                        switch (src[cur + i]) {
                            '.' => {
                                if (std.ascii.isDigit(src[cur + i + 1])) {
                                    typ = .float;
                                    i += 1;
                                }
                            },
                            '/' => {
                                if (src[cur + i + 1] == '/' and std.ascii.isDigit(src[cur + i + 2])) {
                                    i += 2;
                                    typ = .rational;
                                }
                            },
                            else => {},
                        }
                    }
                    if (!std.ascii.isDigit(src[cur + i])) {
                        break;
                    }
                }
                end = i;
            },
            '"' => {
                var i: usize = 1;
                while (src[cur + i] != '"') {
                    i += 1;
                    if (cur + i > src.len) {
                        break;
                    }
                }
                i += 1;
                typ = .string;
                end = i;
            },
            else => {
                const mg = Token.monographs.get(src[cur .. cur + 1]);
                if (mg != null) {
                    typ = mg.?;
                    end = 1;
                }
                if (cur + 1 < src.len) {
                    const dg = Token.digraphs.get(src[cur .. cur + 2]);
                    if (dg != null) {
                        typ = dg.?;
                        end = 2;
                    }
                }
            },
        }
        const pos = Token.Pos{ .start = cur, .end = cur + end };
        cur += end;
        const tok = Token{ .type = typ, .pos = pos };
        tokens.append(tok) catch {
            continue;
        };
    }
    return tokens.items;
}

pub fn main() void {
    const src = "test 123 \"string\";";
    const allocator = std.heap.page_allocator;
    const toks = tokenise(allocator, src);
    for (toks) |tok| {
        print("tok: {s}\n", .{src[tok.pos.start..tok.pos.end]});
    }
}
