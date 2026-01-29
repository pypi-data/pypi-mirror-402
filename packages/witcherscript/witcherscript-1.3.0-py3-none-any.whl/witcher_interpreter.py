#!/usr/bin/env python3
"""
WitcherScript Interpreter
A programming language inspired by The Witcher 3
"""

import re
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum

class TokenType(Enum):
    # Literals
    NUMBER = "NUMBER"
    TEXT = "TEXT"
    TRUTH = "TRUTH"
    FALSEHOOD = "FALSEHOOD"
    IDENTIFIER = "IDENTIFIER"

    # Keywords (Witcher Signs)
    IGNI = "IGNI"  # if
    QUEN = "QUEN"  # while
    YRDEN = "YRDEN"  # for
    AARD = "AARD"  # function def
    AXII = "AXII"  # switch
    ELIXIR = "ELIXIR"  # else
    CONTRACT = "CONTRACT"  # var declaration
    HUNT = "HUNT"  # return
    MUTATION = "MUTATION"  # const
    MEDALLION = "MEDALLION"  # print
    GRIMOIRE = "GRIMOIRE"  # import

    # Operators
    PLUS = "PLUS"
    MINUS = "MINUS"
    STAR = "STAR"
    SLASH = "SLASH"
    PERCENT = "PERCENT"
    EQ = "EQ"
    EQEQ = "EQEQ"
    NEQ = "NEQ"
    LT = "LT"
    GT = "GT"
    LTEQ = "LTEQ"
    GTEQ = "GTEQ"
    AND = "AND"
    OR = "OR"
    NOT = "NOT"

    # Delimiters
    LPAREN = "LPAREN"
    RPAREN = "RPAREN"
    LBRACE = "LBRACE"
    RBRACE = "RBRACE"
    LBRACKET = "LBRACKET"
    RBRACKET = "RBRACKET"
    COMMA = "COMMA"
    ARROW = "ARROW"

    # Special
    NEWLINE = "NEWLINE"
    EOF = "EOF"

class Token:
    def __init__(self, type_: TokenType, value: Any, line: int, col: int):
        self.type = type_
        self.value = value
        self.line = line
        self.col = col

    def __repr__(self):
        return f"Token({self.type.name}, {self.value!r}, {self.line}:{self.col})"

class Lexer:
    KEYWORDS = {
        'igni': TokenType.IGNI,
        'quen': TokenType.QUEN,
        'yrden': TokenType.YRDEN,
        'aard': TokenType.AARD,
        'axii': TokenType.AXII,
        'elixir': TokenType.ELIXIR,
        'contract': TokenType.CONTRACT,
        'hunt': TokenType.HUNT,
        'mutation': TokenType.MUTATION,
        'medallion': TokenType.MEDALLION,
        'grimoire': TokenType.GRIMOIRE,
        'truth': TokenType.TRUTH,
        'falsehood': TokenType.FALSEHOOD,
        'and': TokenType.AND,
        'or': TokenType.OR,
        'not': TokenType.NOT,
    }

    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.col = 1
        self.tokens: List[Token] = []

    def error(self, message: str):
        raise SyntaxError(f"Lexer error at {self.line}:{self.col}: {message}")

    def current_char(self) -> Optional[str]:
        if self.pos >= len(self.source):
            return None
        return self.source[self.pos]

    def peek_char(self, offset: int = 1) -> Optional[str]:
        pos = self.pos + offset
        if pos >= len(self.source):
            return None
        return self.source[pos]

    def advance(self):
        if self.pos < len(self.source):
            if self.source[self.pos] == '\n':
                self.line += 1
                self.col = 1
            else:
                self.col += 1
            self.pos += 1

    def skip_whitespace(self):
        while self.current_char() and self.current_char() in ' \t\r':
            self.advance()

    def skip_comment(self):
        if self.current_char() == '#':
            while self.current_char() and self.current_char() != '\n':
                self.advance()

    def read_string(self, quote: str) -> str:
        self.advance()  # skip opening quote
        value = ""
        while self.current_char() and self.current_char() != quote:
            if self.current_char() == '\\':
                self.advance()
                if self.current_char() == 'n':
                    value += '\n'
                elif self.current_char() == 't':
                    value += '\t'
                elif self.current_char() == '\\':
                    value += '\\'
                elif self.current_char() == quote:
                    value += quote
                else:
                    value += self.current_char()
                self.advance()
            else:
                value += self.current_char()
                self.advance()

        if not self.current_char():
            self.error("Unterminated string")

        self.advance()  # skip closing quote
        return value

    def read_number(self) -> float:
        num_str = ""
        while self.current_char() and (self.current_char().isdigit() or self.current_char() == '.'):
            num_str += self.current_char()
            self.advance()

        if '.' in num_str:
            return float(num_str)
        return float(num_str)

    def read_identifier(self) -> str:
        ident = ""
        while self.current_char() and (self.current_char().isalnum() or self.current_char() == '_'):
            ident += self.current_char()
            self.advance()
        return ident

    def tokenize(self) -> List[Token]:
        while self.pos < len(self.source):
            self.skip_whitespace()

            if not self.current_char():
                break

            # Comments
            if self.current_char() == '#':
                self.skip_comment()
                continue

            line, col = self.line, self.col

            # Newline
            if self.current_char() == '\n':
                self.tokens.append(Token(TokenType.NEWLINE, '\n', line, col))
                self.advance()
                continue

            # Strings
            if self.current_char() in '"\'':
                quote = self.current_char()
                value = self.read_string(quote)
                self.tokens.append(Token(TokenType.TEXT, value, line, col))
                continue

            # Numbers
            if self.current_char().isdigit():
                value = self.read_number()
                self.tokens.append(Token(TokenType.NUMBER, value, line, col))
                continue

            # Identifiers and keywords
            if self.current_char().isalpha() or self.current_char() == '_':
                ident = self.read_identifier()
                token_type = self.KEYWORDS.get(ident, TokenType.IDENTIFIER)
                self.tokens.append(Token(token_type, ident, line, col))
                continue

            # Operators and delimiters
            ch = self.current_char()

            if ch == '+':
                self.tokens.append(Token(TokenType.PLUS, '+', line, col))
                self.advance()
            elif ch == '-':
                if self.peek_char() == '>':
                    self.tokens.append(Token(TokenType.ARROW, '->', line, col))
                    self.advance()
                    self.advance()
                else:
                    self.tokens.append(Token(TokenType.MINUS, '-', line, col))
                    self.advance()
            elif ch == '*':
                self.tokens.append(Token(TokenType.STAR, '*', line, col))
                self.advance()
            elif ch == '/':
                self.tokens.append(Token(TokenType.SLASH, '/', line, col))
                self.advance()
            elif ch == '%':
                self.tokens.append(Token(TokenType.PERCENT, '%', line, col))
                self.advance()
            elif ch == '=':
                if self.peek_char() == '=':
                    self.tokens.append(Token(TokenType.EQEQ, '==', line, col))
                    self.advance()
                    self.advance()
                else:
                    self.tokens.append(Token(TokenType.EQ, '=', line, col))
                    self.advance()
            elif ch == '!':
                if self.peek_char() == '=':
                    self.tokens.append(Token(TokenType.NEQ, '!=', line, col))
                    self.advance()
                    self.advance()
                else:
                    self.tokens.append(Token(TokenType.NOT, '!', line, col))
                    self.advance()
            elif ch == '<':
                if self.peek_char() == '=':
                    self.tokens.append(Token(TokenType.LTEQ, '<=', line, col))
                    self.advance()
                    self.advance()
                else:
                    self.tokens.append(Token(TokenType.LT, '<', line, col))
                    self.advance()
            elif ch == '>':
                if self.peek_char() == '=':
                    self.tokens.append(Token(TokenType.GTEQ, '>=', line, col))
                    self.advance()
                    self.advance()
                else:
                    self.tokens.append(Token(TokenType.GT, '>', line, col))
                    self.advance()
            elif ch == '(':
                self.tokens.append(Token(TokenType.LPAREN, '(', line, col))
                self.advance()
            elif ch == ')':
                self.tokens.append(Token(TokenType.RPAREN, ')', line, col))
                self.advance()
            elif ch == '{':
                self.tokens.append(Token(TokenType.LBRACE, '{', line, col))
                self.advance()
            elif ch == '}':
                self.tokens.append(Token(TokenType.RBRACE, '}', line, col))
                self.advance()
            elif ch == '[':
                self.tokens.append(Token(TokenType.LBRACKET, '[', line, col))
                self.advance()
            elif ch == ']':
                self.tokens.append(Token(TokenType.RBRACKET, ']', line, col))
                self.advance()
            elif ch == ',':
                self.tokens.append(Token(TokenType.COMMA, ',', line, col))
                self.advance()
            else:
                self.error(f"Unexpected character: {ch}")

        self.tokens.append(Token(TokenType.EOF, None, self.line, self.col))
        return self.tokens

# AST Nodes
class ASTNode:
    pass

class Number(ASTNode):
    def __init__(self, value: float):
        self.value = value

class String(ASTNode):
    def __init__(self, value: str):
        self.value = value

class Boolean(ASTNode):
    def __init__(self, value: bool):
        self.value = value

class Identifier(ASTNode):
    def __init__(self, name: str):
        self.name = name

class BinaryOp(ASTNode):
    def __init__(self, left: ASTNode, op: Token, right: ASTNode):
        self.left = left
        self.op = op
        self.right = right

class UnaryOp(ASTNode):
    def __init__(self, op: Token, operand: ASTNode):
        self.op = op
        self.operand = operand

class Assignment(ASTNode):
    def __init__(self, name: str, value: ASTNode):
        self.name = name
        self.value = value

class ArrayAssignment(ASTNode):
    def __init__(self, obj: ASTNode, index: ASTNode, value: ASTNode):
        self.obj = obj
        self.index = index
        self.value = value

class VarDeclaration(ASTNode):
    def __init__(self, name: str, value: ASTNode, is_constant: bool = False):
        self.name = name
        self.value = value
        self.is_constant = is_constant

class FunctionCall(ASTNode):
    def __init__(self, name: str, args: List[ASTNode]):
        self.name = name
        self.args = args

class IfStatement(ASTNode):
    def __init__(self, condition: ASTNode, then_body: List[ASTNode], else_body: Optional[List[ASTNode]] = None):
        self.condition = condition
        self.then_body = then_body
        self.else_body = else_body

class WhileLoop(ASTNode):
    def __init__(self, condition: ASTNode, body: List[ASTNode]):
        self.condition = condition
        self.body = body

class ForLoop(ASTNode):
    def __init__(self, var: str, iterable: ASTNode, body: List[ASTNode]):
        self.var = var
        self.iterable = iterable
        self.body = body

class FunctionDef(ASTNode):
    def __init__(self, name: str, params: List[str], body: List[ASTNode]):
        self.name = name
        self.params = params
        self.body = body

class ReturnStatement(ASTNode):
    def __init__(self, value: Optional[ASTNode] = None):
        self.value = value

class Array(ASTNode):
    def __init__(self, elements: List[ASTNode]):
        self.elements = elements

class IndexAccess(ASTNode):
    def __init__(self, obj: ASTNode, index: ASTNode):
        self.obj = obj
        self.index = index

class Grimoire(ASTNode):
    def __init__(self, path: str):
        self.path = path

class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def error(self, message: str):
        token = self.current_token()
        raise SyntaxError(f"Parser error at {token.line}:{token.col}: {message}")

    def current_token(self) -> Token:
        if self.pos >= len(self.tokens):
            return self.tokens[-1]  # EOF
        return self.tokens[self.pos]

    def peek_token(self, offset: int = 1) -> Token:
        pos = self.pos + offset
        if pos >= len(self.tokens):
            return self.tokens[-1]  # EOF
        return self.tokens[pos]

    def advance(self):
        self.pos += 1

    def skip_newlines(self):
        while self.current_token().type == TokenType.NEWLINE:
            self.advance()

    def expect(self, token_type: TokenType) -> Token:
        token = self.current_token()
        if token.type != token_type:
            self.error(f"Expected {token_type.name}, got {token.type.name}")
        self.advance()
        return token

    def parse(self) -> List[ASTNode]:
        statements = []
        self.skip_newlines()

        while self.current_token().type != TokenType.EOF:
            stmt = self.parse_statement()
            if stmt:
                statements.append(stmt)
            self.skip_newlines()

        return statements

    def parse_statement(self) -> Optional[ASTNode]:
        self.skip_newlines()
        token = self.current_token()

        if token.type == TokenType.CONTRACT:
            return self.parse_var_declaration(is_constant=False)
        elif token.type == TokenType.MUTATION:
            return self.parse_var_declaration(is_constant=True)
        elif token.type == TokenType.IGNI:
            return self.parse_if_statement()
        elif token.type == TokenType.QUEN:
            return self.parse_while_loop()
        elif token.type == TokenType.YRDEN:
            return self.parse_for_loop()
        elif token.type == TokenType.AARD:
            return self.parse_function_def()
        elif token.type == TokenType.HUNT:
            return self.parse_return_statement()
        elif token.type == TokenType.MEDALLION:
            return self.parse_print_statement()
        elif token.type == TokenType.GRIMOIRE:
            return self.parse_grimoire_statement()
        else:
            return self.parse_expression_statement()

    def parse_var_declaration(self, is_constant: bool = False) -> VarDeclaration:
        keyword_token = self.current_token()
        self.advance()  # skip 'contract' or 'mutation'

        name_token = self.expect(TokenType.IDENTIFIER)
        name = name_token.value

        self.expect(TokenType.EQ)
        value = self.parse_expression()

        return VarDeclaration(name, value, is_constant)

    def parse_if_statement(self) -> IfStatement:
        self.advance()  # skip 'igni'

        condition = self.parse_expression()

        self.expect(TokenType.LBRACE)
        self.skip_newlines()

        then_body = self.parse_block()

        self.expect(TokenType.RBRACE)
        self.skip_newlines()

        else_body = None
        if self.current_token().type == TokenType.ELIXIR:
            self.advance()  # skip 'elixir'
            self.expect(TokenType.LBRACE)
            self.skip_newlines()
            else_body = self.parse_block()
            self.expect(TokenType.RBRACE)

        return IfStatement(condition, then_body, else_body)

    def parse_while_loop(self) -> WhileLoop:
        self.advance()  # skip 'quen'

        condition = self.parse_expression()

        self.expect(TokenType.LBRACE)
        self.skip_newlines()

        body = self.parse_block()

        self.expect(TokenType.RBRACE)

        return WhileLoop(condition, body)

    def parse_for_loop(self) -> ForLoop:
        self.advance()  # skip 'yrden'

        var_token = self.expect(TokenType.IDENTIFIER)
        var = var_token.value

        self.expect(TokenType.ARROW)

        iterable = self.parse_expression()

        self.expect(TokenType.LBRACE)
        self.skip_newlines()

        body = self.parse_block()

        self.expect(TokenType.RBRACE)

        return ForLoop(var, iterable, body)

    def parse_function_def(self) -> FunctionDef:
        self.advance()  # skip 'aard'

        name_token = self.expect(TokenType.IDENTIFIER)
        name = name_token.value

        params = []
        self.expect(TokenType.LPAREN)

        if self.current_token().type != TokenType.RPAREN:
            while True:
                param_token = self.expect(TokenType.IDENTIFIER)
                params.append(param_token.value)

                if self.current_token().type != TokenType.COMMA:
                    break
                self.advance()  # skip comma

        self.expect(TokenType.RPAREN)
        self.expect(TokenType.LBRACE)
        self.skip_newlines()

        body = self.parse_block()

        self.expect(TokenType.RBRACE)

        return FunctionDef(name, params, body)

    def parse_return_statement(self) -> ReturnStatement:
        self.advance()  # skip 'hunt'

        value = None
        if self.current_token().type not in (TokenType.NEWLINE, TokenType.EOF):
            value = self.parse_expression()

        return ReturnStatement(value)

    def parse_print_statement(self) -> FunctionCall:
        self.advance()  # skip 'medallion'

        self.expect(TokenType.LPAREN)
        args = []

        if self.current_token().type != TokenType.RPAREN:
            while True:
                args.append(self.parse_expression())
                if self.current_token().type != TokenType.COMMA:
                    break
                self.advance()

        self.expect(TokenType.RPAREN)

        return FunctionCall('medallion', args)

    def parse_grimoire_statement(self) -> Grimoire:
        self.advance()  # skip 'grimoire'
        
        path_token = self.expect(TokenType.TEXT)
        path = path_token.value
        
        return Grimoire(path)

    def parse_block(self) -> List[ASTNode]:
        statements = []

        while self.current_token().type != TokenType.RBRACE:
            self.skip_newlines()

            if self.current_token().type == TokenType.RBRACE:
                break

            stmt = self.parse_statement()
            if stmt:
                statements.append(stmt)

        return statements

    def parse_expression_statement(self) -> Optional[ASTNode]:
        expr = self.parse_expression()
        return expr

    def parse_expression(self) -> ASTNode:
        return self.parse_or_expression()

    def parse_or_expression(self) -> ASTNode:
        left = self.parse_and_expression()

        while self.current_token().type == TokenType.OR:
            op = self.current_token()
            self.advance()
            right = self.parse_and_expression()
            left = BinaryOp(left, op, right)

        return left

    def parse_and_expression(self) -> ASTNode:
        left = self.parse_equality()

        while self.current_token().type == TokenType.AND:
            op = self.current_token()
            self.advance()
            right = self.parse_equality()
            left = BinaryOp(left, op, right)

        return left

    def parse_equality(self) -> ASTNode:
        left = self.parse_comparison()

        while self.current_token().type in (TokenType.EQEQ, TokenType.NEQ):
            op = self.current_token()
            self.advance()
            right = self.parse_comparison()
            left = BinaryOp(left, op, right)

        return left

    def parse_comparison(self) -> ASTNode:
        left = self.parse_additive()

        while self.current_token().type in (TokenType.LT, TokenType.GT, TokenType.LTEQ, TokenType.GTEQ):
            op = self.current_token()
            self.advance()
            right = self.parse_additive()
            left = BinaryOp(left, op, right)

        return left

    def parse_additive(self) -> ASTNode:
        left = self.parse_multiplicative()

        while self.current_token().type in (TokenType.PLUS, TokenType.MINUS):
            op = self.current_token()
            self.advance()
            right = self.parse_multiplicative()
            left = BinaryOp(left, op, right)

        return left

    def parse_multiplicative(self) -> ASTNode:
        left = self.parse_unary()

        while self.current_token().type in (TokenType.STAR, TokenType.SLASH, TokenType.PERCENT):
            op = self.current_token()
            self.advance()
            right = self.parse_unary()
            left = BinaryOp(left, op, right)

        return left

    def parse_unary(self) -> ASTNode:
        if self.current_token().type in (TokenType.NOT, TokenType.MINUS):
            op = self.current_token()
            self.advance()
            operand = self.parse_unary()
            return UnaryOp(op, operand)

        return self.parse_postfix()

    def parse_postfix(self) -> ASTNode:
        expr = self.parse_primary()

        while True:
            if self.current_token().type == TokenType.LBRACKET:
                self.advance()
                index = self.parse_expression()
                self.expect(TokenType.RBRACKET)
                expr = IndexAccess(expr, index)
            elif self.current_token().type == TokenType.LPAREN and isinstance(expr, Identifier):
                self.advance()
                args = []

                if self.current_token().type != TokenType.RPAREN:
                    while True:
                        args.append(self.parse_expression())
                        if self.current_token().type != TokenType.COMMA:
                            break
                        self.advance()

                self.expect(TokenType.RPAREN)
                expr = FunctionCall(expr.name, args)
            elif self.current_token().type == TokenType.EQ:
                if isinstance(expr, Identifier):
                    self.advance()
                    value = self.parse_expression()
                    expr = Assignment(expr.name, value)
                elif isinstance(expr, IndexAccess):
                    self.advance()
                    value = self.parse_expression()
                    expr = ArrayAssignment(expr.obj, expr.index, value)
                else:
                    break
            else:
                break

        return expr

    def parse_primary(self) -> ASTNode:
        token = self.current_token()

        if token.type == TokenType.NUMBER:
            self.advance()
            return Number(token.value)

        elif token.type == TokenType.TEXT:
            self.advance()
            return String(token.value)

        elif token.type == TokenType.TRUTH:
            self.advance()
            return Boolean(True)

        elif token.type == TokenType.FALSEHOOD:
            self.advance()
            return Boolean(False)

        elif token.type == TokenType.IDENTIFIER:
            name = token.value
            self.advance()
            return Identifier(name)

        elif token.type == TokenType.LPAREN:
            self.advance()
            expr = self.parse_expression()
            self.expect(TokenType.RPAREN)
            return expr

        elif token.type == TokenType.LBRACKET:
            self.advance()
            elements = []

            if self.current_token().type != TokenType.RBRACKET:
                while True:
                    elements.append(self.parse_expression())
                    if self.current_token().type != TokenType.COMMA:
                        break
                    self.advance()

            self.expect(TokenType.RBRACKET)
            return Array(elements)

        else:
            self.error(f"Unexpected token: {token.type.name}")

class ReturnValue(Exception):
    def __init__(self, value: Any):
        self.value = value

class Interpreter:
    def __init__(self):
        self.globals: Dict[str, Any] = {}
        self.locals_stack: List[Dict[str, Any]] = []
        self.imported_files: set = set()  # Track imported files to avoid circular imports

    def error(self, message: str):
        raise RuntimeError(message)

    def get_variable(self, name: str) -> Any:
        # Check local scopes from innermost to outermost
        for local_scope in reversed(self.locals_stack):
            if name in local_scope:
                return local_scope[name]

        # Check global scope
        if name in self.globals:
            return self.globals[name]

        self.error(f"Undefined variable: {name}")

    def set_variable(self, name: str, value: Any):
        # If in local scope, update it
        if self.locals_stack:
            self.locals_stack[-1][name] = value
        else:
            # Otherwise, set in global scope
            self.globals[name] = value

    def interpret(self, ast: List[ASTNode]):
        for node in ast:
            self.evaluate(node)

    def evaluate(self, node: ASTNode) -> Any:
        if isinstance(node, Number):
            return node.value

        elif isinstance(node, String):
            return node.value

        elif isinstance(node, Boolean):
            return node.value

        elif isinstance(node, Identifier):
            return self.get_variable(node.name)

        elif isinstance(node, Array):
            return [self.evaluate(elem) for elem in node.elements]

        elif isinstance(node, BinaryOp):
            left = self.evaluate(node.left)
            right = self.evaluate(node.right)

            if node.op.type == TokenType.PLUS:
                # Allow string concatenation with type conversion
                if isinstance(left, str) or isinstance(right, str):
                    return str(left) + str(right)
                return left + right
            elif node.op.type == TokenType.MINUS:
                return left - right
            elif node.op.type == TokenType.STAR:
                return left * right
            elif node.op.type == TokenType.SLASH:
                if right == 0:
                    self.error("Division by zero!")
                return left / right
            elif node.op.type == TokenType.PERCENT:
                return left % right
            elif node.op.type == TokenType.EQEQ:
                return left == right
            elif node.op.type == TokenType.NEQ:
                return left != right
            elif node.op.type == TokenType.LT:
                return left < right
            elif node.op.type == TokenType.GT:
                return left > right
            elif node.op.type == TokenType.LTEQ:
                return left <= right
            elif node.op.type == TokenType.GTEQ:
                return left >= right
            elif node.op.type == TokenType.AND:
                return left and right
            elif node.op.type == TokenType.OR:
                return left or right

        elif isinstance(node, UnaryOp):
            operand = self.evaluate(node.operand)

            if node.op.type == TokenType.MINUS:
                return -operand
            elif node.op.type == TokenType.NOT:
                return not operand

        elif isinstance(node, VarDeclaration):
            value = self.evaluate(node.value)
            self.set_variable(node.name, value)
            return value

        elif isinstance(node, Assignment):
            value = self.evaluate(node.value)
            self.set_variable(node.name, value)
            return value
        
        elif isinstance(node, ArrayAssignment):
            obj = self.evaluate(node.obj)
            index = self.evaluate(node.index)
            value = self.evaluate(node.value)
            
            if isinstance(index, float):
                index = int(index)
            
            if isinstance(obj, list):
                obj[index] = value
            else:
                self.error(f"Cannot index {type(obj).__name__}")
            
            return value

        elif isinstance(node, IfStatement):
            condition = self.evaluate(node.condition)

            if condition:
                for stmt in node.then_body:
                    self.evaluate(stmt)
            elif node.else_body:
                for stmt in node.else_body:
                    self.evaluate(stmt)

        elif isinstance(node, WhileLoop):
            while self.evaluate(node.condition):
                for stmt in node.body:
                    self.evaluate(stmt)

        elif isinstance(node, ForLoop):
            iterable = self.evaluate(node.iterable)

            if not isinstance(iterable, list):
                self.error(f"Cannot iterate over {type(iterable).__name__}")

            for item in iterable:
                self.set_variable(node.var, item)
                for stmt in node.body:
                    self.evaluate(stmt)

        elif isinstance(node, FunctionDef):
            self.set_variable(node.name, node)
            return node

        elif isinstance(node, FunctionCall):
            return self.call_function(node.name, node.args)

        elif isinstance(node, ReturnStatement):
            value = None
            if node.value:
                value = self.evaluate(node.value)
            raise ReturnValue(value)

        elif isinstance(node, IndexAccess):
            obj = self.evaluate(node.obj)
            index = self.evaluate(node.index)

            if isinstance(index, float):
                index = int(index)

            try:
                return obj[index]
            except (IndexError, KeyError, TypeError):
                self.error(f"Invalid index access")

        elif isinstance(node, Grimoire):
            return self.import_grimoire(node.path)

    def call_function(self, name: str, args: List[ASTNode]) -> Any:
        # Built-in functions
        if name == 'medallion':  # print
            values = [str(self.evaluate(arg)) for arg in args]
            print(' '.join(values))
            return None

        elif name == 'sigh':  # input
            return input(self.evaluate(args[0]) if args else "")

        elif name == 'witcher_speed':  # string repeat
            text = str(self.evaluate(args[0]))
            times = int(self.evaluate(args[1]))
            return text * times

        elif name == 'monster_count':  # length
            obj = self.evaluate(args[0])
            return len(obj)

        elif name == 'add_to_bestiary':  # append
            bestiary = self.evaluate(args[0])
            value = self.evaluate(args[1])
            bestiary.append(value)
            return bestiary

        elif name == 'hunter_instinct':  # type info
            value = self.evaluate(args[0])
            if isinstance(value, bool):
                return "truth" if value else "falsehood"
            elif isinstance(value, (int, float)):
                return "number"
            elif isinstance(value, str):
                return "text"
            elif isinstance(value, list):
                return "bestiary"
            else:
                return "unknown"

        elif name == 'potion_effect':  # special arithmetic
            a = self.evaluate(args[0])
            b = self.evaluate(args[1])
            return a + b

        else:
            # User-defined function
            func_def = self.get_variable(name)

            if not isinstance(func_def, FunctionDef):
                self.error(f"'{name}' is not a function")

            if len(args) != len(func_def.params):
                self.error(f"Function '{name}' expects {len(func_def.params)} arguments, got {len(args)}")

            # Create new local scope
            local_scope = {}
            for i, param in enumerate(func_def.params):
                local_scope[param] = self.evaluate(args[i])

            self.locals_stack.append(local_scope)

            try:
                result = None
                for stmt in func_def.body:
                    self.evaluate(stmt)
                return result
            except ReturnValue as ret:
                return ret.value
            finally:
                self.locals_stack.pop()

    def import_grimoire(self, path: str):
        """Import functions and variables from another .witcher file"""
        import os
        
        # Resolve file path
        abs_path = os.path.abspath(path)
        
        # Check for circular imports
        if abs_path in self.imported_files:
            self.error(f"Circular import detected: {path}")
        
        # Check if file exists
        if not os.path.exists(abs_path):
            self.error(f"Grimoire file not found: {path}")
        
        # Mark as imported
        self.imported_files.add(abs_path)
        
        # Read and execute the file
        try:
            with open(abs_path, 'r') as f:
                source = f.read()
            
            lexer = Lexer(source)
            tokens = lexer.tokenize()
            parser = Parser(tokens)
            ast = parser.parse()
            
            # Execute in current global scope (functions will be registered)
            for node in ast:
                self.evaluate(node)
        
        except (SyntaxError, RuntimeError) as e:
            self.error(f"Error importing {path}: {e}")

def run_witcher_script(source: str):
    """Main entry point to run a Witcher script"""
    try:
        lexer = Lexer(source)
        tokens = lexer.tokenize()

        parser = Parser(tokens)
        ast = parser.parse()

        interpreter = Interpreter()
        interpreter.interpret(ast)

    except (SyntaxError, RuntimeError) as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        # Read from file
        with open(sys.argv[1], 'r') as f:
            source = f.read()
        run_witcher_script(source)
    else:
        # Interactive mode
        print("=== WitcherScript Interpreter ===")
        print("Type your Witcher code. Use 'quit' to exit.")
        print()

        lines = []
        while True:
            try:
                line = input("witcher> " if not lines else "       > ")
                if line.lower() == "quit":
                    break

                lines.append(line)

                # Try to parse and execute
                source = '\n'.join(lines)

                try:
                    lexer = Lexer(source)
                    tokens = lexer.tokenize()
                    parser = Parser(tokens)
                    ast = parser.parse()

                    interpreter = Interpreter()
                    interpreter.interpret(ast)

                    lines = []
                except SyntaxError as e:
                    print(f"  {e}")

            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except EOFError:
                break
