
#region IMPORTS

from abc import ABC, abstractmethod
from colorama import Fore, Back
from string import ascii_letters
from types import FunctionType, BuiltinFunctionType
from time import sleep
import requests
import json
import math
import random
from pathlib import Path
from platformdirs import user_config_dir

#endregion

#region CONSOLE

def color(message: str, background: str, foreground: str = Fore.BLACK):
    return background + foreground + message + Fore.RESET + Back.RESET

def string_with_arrows(start_position, end_position):
    result = ''
    text = start_position.file_text

    # Calculate indices
    index_start = max(text.rfind('\n', 0, start_position.index), 0)
    index_end = text.find('\n', index_start + 1)
    if index_end < 0: index_end = len(text)
    
    # Generate each line
    line_count = end_position.line - start_position.line + 1

    for i in range(line_count):
        # Calculate line columns
        line = text[index_start: index_end]

        column_start = start_position.column if i == 0 else 0
        column_end = end_position.column if i == line_count - 1 else len(line) - 1

        # Append to result
        result += line + '\n'
        result += ' ' * column_start + '^' * (column_end - column_start)

        # Re-calculate indices
        index_start = index_end
        index_end = text.find('\n', index_start + 1)

        if index_end < 0: index_end = len(text)

    return result.replace('\t', '')

#endregion

#region ERRORS

class Error:
    def __init__(self, start_position, end_position, error_name, details):
        self.start_position = start_position
        self.end_position = end_position
        self.error_name = error_name
        self.details = details

    def as_string(self):
        return f"""{color(self.error_name + ':', Back.RED)} {self.details}
File: {self.start_position.file_name}
From: Line {self.start_position.line + 1}, character {self.start_position.column + 1}
To: Line {self.end_position.line + 1}, character {self.end_position.column + 1}

{string_with_arrows(self.start_position, self.end_position)}"""
    
    def __repr__(self) -> str:
        return self.as_string()
    
class IllegalCharacterError(Error):
    def __init__(self, start_position, end_position, details):
        super().__init__(start_position, end_position, 'Illegal Character', details)

class InvalidSyntaxError(Error):
    def __init__(self, start_position, end_position, details):
        super().__init__(start_position, end_position, 'Invalid Syntax', details)

class ExpectedCharacterError(Error):
    def __init__(self, start_position, end_position, details):
        super().__init__(start_position, end_position, 'Expected Character', details)

class RuntimeError(Error):
    def __init__(self, start_position, end_position, details, context):
        super().__init__(start_position, end_position, 'Runtime Error', details)
        self.context = context

    def as_string(self) -> str:
        output = super().as_string()
        output += "\n\n" + self.generate_traceback()

        return output
    
    def generate_traceback(self) -> str:
        output = ''
        position = self.start_position.copy()
        context = self.context

        while context:
            output = f'\nFile: {position.file_name}. Line {position.line + 1}, in {context.display_name}' + output
            position = context.parent_entry_position
            context = context.parent

        return color('Traceback:', Back.LIGHTBLUE_EX) + output

#endregion


#region POSITION

class Position:
    def __init__(self, index, line, column, file_name = None, file_text = None):
        self.index = index
        self.line = line
        self.column = column
        self.file_name = file_name
        self.file_text = file_text

    def advance(self, current_character = None):
        self.index += 1
        self.column += 1

        if current_character == '\n':
            self.line += 1
            self.column = 0

        return self
    
    def copy(self):
        return Position(self.index, self.line, self.column, self.file_name, self.file_text)
    
    def __repr__(self) -> str:
        return f'Index: {self.index}, Line: {self.line}, Column: {self.column}'

#endregion

#region TOKENS

# TT = Token Type

## Math Expressions
TT_NUMBER = "NUMBER"
TT_ADD = "ADD"
TT_SUBTRACT = "SUBTRACT"
TT_MULIPLY = "MULTIPLY"
TT_DIVIDE = "DIVIDE"
TT_POWER = "POWER"

## Text
TT_TEXT = "TEXT"

## Lists
TT_OPEN_BRACKETS = "OPEN_BRACKETS"
TT_CLOSE_BRACKETS = "CLOSE_BRACKETS"

## Dictionaries
TT_PIPE = "PIPE"
TT_COLON = "COLON"

## Comparaisons
TT_DOUBLE_EQUALS = "DOUBLE_EQUALS"
TT_NOT_EQUALS = "NOT_EQUALS"
TT_LESS_THAN = "LESS_THAN"
TT_GREATER_THAN = "GREATER_THAN"
TT_LESS_THAN_OR_EQUALS = "LESS_THAN_OR_EQUALS"
TT_GREATER_THAN_OR_EQUALS = "GREATER_THAN_OR_EQUALS"

COMPARAISON_TOKEN_TYPES = (
    TT_DOUBLE_EQUALS,
    TT_NOT_EQUALS,
    TT_LESS_THAN,
    TT_GREATER_THAN,
    TT_LESS_THAN_OR_EQUALS,
    TT_GREATER_THAN_OR_EQUALS
)

## Variables
TT_VARIABLE = "VARIABLE"
TT_IDENTIFIER = "IDENTIFIER"
TT_EQUALS = "EQUALS"

## General
TT_KEYWORD = "KEYWORD"

KEYWORDS = ['and', 'or', 'not', 'global', 'default', 'if', 'else', 'while']

TT_DOT = "DOT"
TT_COMMA = "COMMA"
TT_OPEN_PARENTHESIS = "OPEN_PARENTHESIS"
TT_CLOSE_PARENTHESIS = "CLOSE_PARENTHESIS"

TT_NEW_LINE = "NEW_LINE"
TT_EOF = "EOF"

class Token:
    def __init__(self, type_, value = None, start_position: Position | None = None, end_position: Position | None = None):
        self.type = type_
        self.value = value
        self.start_position = start_position.copy() if start_position else None
        self.end_position = end_position.copy() if end_position else None

        if self.start_position and not self.end_position:
            self.end_position = self.start_position.copy()
            self.end_position.advance()

    def matches(self, type_, value) -> bool:
        return (self.type == type_) and (self.value == value)

    def __repr__(self):
        return self.type + (f": {self.value}" if self.value else "")
    
#endregion

#region LEXER

DIGITS = '0123456789'
LETTERS = ascii_letters
LETTERS_DIGITS = LETTERS + DIGITS

class Lexer:
    def __init__(self, file_name, text):
        self.file_name = file_name
        self.text = text
        self.position = Position(0, 0, 0, file_name, text)
        self.solve_current_character()

    def solve_current_character(self):
        if self.position.index < len(self.text):
            self.current_character = self.text[self.position.index]
        else:
            self.current_character = None

    def advance(self):
        self.position.advance(self.current_character)
        self.solve_current_character()

    def make_tokens(self):
        tokens = []

        while self.current_character != None:
            ## General
            if self.current_character in ' \t':
                pass
            elif self.current_character in ';\n':
                tokens.append(Token(TT_NEW_LINE, start_position = self.position))
            elif self.current_character in DIGITS:
                tokens.append(self.make_number())
                continue
            elif self.current_character in LETTERS:
                tokens.append(self.make_identifier())
                continue
            elif self.current_character == '.':
                tokens.append(Token(TT_DOT, start_position = self.position))
            elif self.current_character == ',':
                tokens.append(Token(TT_COMMA, start_position = self.position))
            elif self.current_character == '(':
                tokens.append(Token(TT_OPEN_PARENTHESIS, start_position = self.position))
            elif self.current_character == ')':
                tokens.append(Token(TT_CLOSE_PARENTHESIS, start_position = self.position))
            
            ## Math expressions
            elif self.current_character == '+':
                tokens.append(Token(TT_ADD, start_position = self.position))
            elif self.current_character == '-':
                tokens.append(Token(TT_SUBTRACT, start_position = self.position))
            elif self.current_character == '*':
                tokens.append(Token(TT_MULIPLY, start_position = self.position))
            elif self.current_character == '/':
                token = self.make_divide_or_comment()

                if token is not None:
                    tokens.append(token)

                continue
            elif self.current_character == '^':
                tokens.append(Token(TT_POWER, start_position = self.position))

            ## Text
            elif self.current_character in '"{}':
                token, error = self.make_text()
                if error: return [], error

                tokens.append(token)
                continue

            ## Lists
            elif self.current_character == '[':
                tokens.append(Token(TT_OPEN_BRACKETS, start_position = self.position))
            elif self.current_character == ']':
                tokens.append(Token(TT_CLOSE_BRACKETS, start_position = self.position))

            ## Dictionaries
            elif self.current_character == "|":
                tokens.append(Token(TT_PIPE, start_position = self.position))
            elif self.current_character == ":":
                tokens.append(Token(TT_COLON, start_position = self.position))
            
            ## Comparisons
            elif self.current_character == '=':
                tokens.append(self.make_equals())
                continue
            elif self.current_character == '!':
                token, error = self.make_not_equals()
                if error: return [], error

                tokens.append(token)
                continue
            elif self.current_character == '<':
                tokens.append(self.make_less_than())
                continue
            elif self.current_character == '>':
                tokens.append(self.make_greater_than())
                continue

            ## Variables
            elif self.current_character == '$':
                tokens.append(Token(TT_VARIABLE, start_position = self.position))

            ##

            else:
                character = self.current_character

                start_position = self.position.copy()
                self.advance()
                end_position = self.position.copy()

                return [], IllegalCharacterError(start_position, end_position, character)

            self.advance()

        tokens.append(Token(TT_EOF, start_position = self.position))
        return tokens, None
    
    def make_number(self):
        number_string = ''
        has_dot = False
        start_position = self.position.copy()

        while self.current_character != None and self.current_character in DIGITS + '.':
            if self.current_character == '.':
                if has_dot: break

                has_dot = True
                number_string += '.'
            else:
                number_string += self.current_character

            self.advance()

        return Token(TT_NUMBER, float(number_string), start_position, self.position.copy())
    
    def make_text(self):
        text = ''
        start_position = self.position.copy()

        symbol = self.current_character
        self.advance()

        if symbol == '"':
            while self.current_character != None and not self.current_character == symbol:
                text += self.current_character
                self.advance()

            if self.current_character == symbol:
                self.advance()

                return Token(TT_TEXT, text, start_position, self.position.copy()), None
            
            return None, ExpectedCharacterError(
                start_position, self.position,
                "'\"'"
            )
        
        bracket_count = 1

        while True:
            character = self.current_character

            if character == '{':
                bracket_count += 1
            if character == '}':
                bracket_count -= 1

            if bracket_count == 0:
                self.advance()

                return Token(TT_TEXT, text, start_position, self.position.copy()), None

            if not character is None:
                text += character
            else:
                if bracket_count == 1:
                    return None, ExpectedCharacterError(
                        start_position, self.position,
                        "'}'"
                    )
                else:
                    return None, InvalidSyntaxError(
                        start_position, self.position,
                        "Unterminated text literal"
                    )
                
            self.advance()
    
    def make_identifier(self):
        identifier_string = ''
        start_position = self.position.copy()

        while (self.current_character != None) and (self.current_character in LETTERS_DIGITS + '_~'):
            identifier_string += self.current_character
            self.advance()

        token_type = TT_KEYWORD if identifier_string in KEYWORDS else TT_IDENTIFIER
        return Token(token_type, identifier_string, start_position, self.position)
    
    def make_not_equals(self):
        start_position = self.position.copy()
        self.advance()

        if self.current_character == '=':
            self.advance()
            return Token(TT_NOT_EQUALS, start_position = start_position, end_position = self.position), None
        
        self.advance()
        return None, ExpectedCharacterError(start_position, self.position, "'=' after '!'")
    
    def make_equals(self):
        token_type = TT_EQUALS
        start_position = self.position.copy()

        self.advance()

        if self.current_character == '=':
            self.advance()
            token_type = TT_DOUBLE_EQUALS

        return Token(token_type, start_position = start_position, end_position = self.position)
    
    def make_less_than(self):
        token_type = TT_LESS_THAN
        start_position = self.position.copy()
        
        self.advance()

        if self.current_character == '=':
            self.advance()
            token_type = TT_LESS_THAN_OR_EQUALS

        return Token(token_type, start_position = start_position, end_position = self.position)
    
    def make_greater_than(self):
        token_type = TT_GREATER_THAN
        start_position = self.position.copy()
        
        self.advance()

        if self.current_character == '=':
            self.advance()
            token_type = TT_GREATER_THAN_OR_EQUALS

        return Token(token_type, start_position = start_position, end_position = self.position)
        
    def make_divide_or_comment(self):
        start_position = self.position.copy()
        self.advance()

        if self.current_character == '/':
            while self.current_character is not None and not self.current_character in ';\n':
                self.advance()

            return None
        
        if self.current_character == '*':
            while self.current_character is not None:
                previous_character = self.current_character
                self.advance()
                
                if self.current_character == '/' and previous_character == '*':
                    self.advance()
                    break

            return None

        return Token(TT_DIVIDE, start_position = start_position, end_position = self.position)

#endregion


#region NODES

class Node:
    def __init__(self, start_position: Position | None = None, end_position: Position | None = None):
        self.start_position = start_position
        self.end_position = end_position

    def __repr__(self):
        return f'({self.token})'

## Numbers

class NumberNode(Node):
    def __init__(self, token: Token):
        super().__init__(token.start_position, token.end_position)
        self.token = token

## Expressions

class BinaryOperationNode(Node):
    def __init__(self, left_node: Node, operator_token: Token, right_node: Node):
        super().__init__(left_node.start_position, right_node.end_position)
        
        self.left_node = left_node
        self.operator_token = operator_token
        self.right_node = right_node

    def __repr__(self):
        return f'({self.left_node} {self.operator_token} {self.right_node})'

class UnaryOperationNode(Node):
    def __init__(self, operation_token: Token, node: Node):
        super().__init__(operation_token.start_position, node.end_position)

        self.operation_token = operation_token
        self.node = node

    def __repr__(self) -> str:
        return f'({self.operation_token}, {self.node})'
    
## Text

class TextNode(Node):
    def __init__(self, token: Token):
        super().__init__(token.start_position, token.end_position)
        self.token = token

class CallNode(Node):
    def __init__(self, node_to_call: Node, argument_nodes: list[Node]):
        super().__init__(node_to_call.start_position, node_to_call.end_position)

        self.node_to_call = node_to_call
        self.argument_nodes = argument_nodes

        if (len(argument_nodes) > 0):
            self.end_position = argument_nodes[len(argument_nodes) - 1].end_position

    def __repr__(self):
        return f'(CallNode: {self.node_to_call}({", ".join(str(x) for x in self.argument_nodes)}))'

## Lists

class ListNode(Node):
    def __init__(self, element_nodes: list[Node], start_position: Position, end_position: Position):
        super().__init__(start_position, end_position)
        self.element_nodes = element_nodes

    def __repr__(self):
        return f'([{", ".join(str(x) for x in self.element_nodes)}])'

class IndexingNode(Node):
    def __init__(self, base_node: Node, index_node: Node, allow_methods: bool = False):
        super().__init__(base_node.start_position, index_node.end_position)

        self.base_node = base_node
        self.index_node = index_node
        self.allow_methods = allow_methods

    def __repr__(self):
        return f'({self.base_node}[{self.index_node}])'

class IndexAssignmentNode(Node):
    def __init__(self, variable_node: Node, indexing_node: IndexingNode, value_node: Node):
        super().__init__(indexing_node.start_position, value_node.end_position)

        self.variable_node = variable_node
        self.indexing_node = indexing_node
        self.value_node = value_node

## Dictionaries

class DictionaryNode(Node):
    def __init__(self, node_dictionary: dict[Node, Node], start_position: Position, end_position: Position):
        super().__init__(start_position, end_position)
        self.node_dictionary = node_dictionary

    def __repr__(self):
        return f'(|{str(self.node_dictionary).removeprefix("{").removesuffix("}")}|'

## Variables

class VariableNode(Node):
    def __init__(self, variable_name_node: Node, scope_node: Node | None):
        super().__init__(variable_name_node.start_position, variable_name_node.end_position)

        self.variable_name_node = variable_name_node
        self.scope_node = scope_node

        if scope_node:
            new_position = scope_node.start_position.copy()
            new_position.index -= 1
            new_position.column -= 1

            self.start_position = new_position

    def __repr__(self):
        return f'(<{self.scope_node}>{self.variable_name_node})'

class VariableAccessNode(Node):
    def __init__(self, variable_node: Node):
        super().__init__(variable_node.start_position, variable_node.end_position)
        self.variable_node = variable_node

    def __repr__(self):
        return f'(VariableAccessNode: {self.variable_node})'

class VariableAssignmentNode(Node):
    def __init__(self, variable_node: Node, value_node: Node):
        super().__init__(variable_node.start_position, value_node.end_position)

        self.variable_node = variable_node
        self.value_node = value_node

    def __repr__(self):
        return f'(VariableAssignmentNode: {self.variable_node} = {self.value_node})'

class GlobalScopeNode(Node):
    def __init__(self, token: Token):
        super().__init__(token.start_position, token.end_position)

    def __repr__(self):
        return '(GlobalScopeNode)'
    
class DefaultScopeNode(Node):
    def __init__(self, token: Token):
        super().__init__(token.start_position, token.end_position)

    def __repr__(self):
        return '(DefaultScopeNode)'

## Null

class NullNode(Node):
    def __init__(self, start_position: Position, end_position: Position):
        super().__init__(start_position, end_position)

    def __repr__(self):
        return repr(Null())

## Flow Control

class IfNode(Node):
    def __init__(self, condition_node: Node, true_node: Node, false_node: Node | None = None):
        start_position = condition_node.start_position.copy()
        start_position.index -= 1
        start_position.column -= 1

        super().__init__(start_position, true_node.end_position)

        self.condition_node = condition_node
        self.true_node = true_node
        self.false_node = false_node

class WhileNode(Node):
    def __init__(self, condition_node: Node, while_node: Node):
        start_position = condition_node.start_position.copy()
        start_position.index -= 1
        start_position.column -= 1

        super().__init__(start_position, while_node.end_position)

        self.condition_node = condition_node
        self.while_node = while_node

## General

class ValueNode(Node):
    def __init__(self, value):
        super().__init__(value.start_position, value.end_position)
        self.value = value

#endregion

#region PARSE RESULT

class ParseResult:
    def __init__(self):
        self.error = None
        self.node = None
        self.advance_count = 0
        self.to_reverse_count = 0

    def register_advancement(self):
        self.advance_count += 1
    
    def register(self, result):
        self.advance_count += result.advance_count

        if result.error: self.error = result.error
        return result.node
    
    def try_register(self, result):
        if result.error:
            self.to_reverse_count = result.advance_count
            return None
        
        return self.register(result)
    
    def success(self, node):
        self.node = node
        return self
    
    def failure(self, error):
        if not self.error or self.advance_count == 0:
            self.error = error

        return self

#endregion

#region PARSER

class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.current_token_index = 0
        self.solve_current_token()

        self.last_postfix_is_index = False

    def solve_current_token(self):
        if self.current_token_index < len(self.tokens):
            self.current_token = self.tokens[self.current_token_index]
        
    def advance(self):
        self.current_token_index += 1
        self.solve_current_token()

        return self.current_token
    
    def reverse(self, amount = 1):
        self.current_token_index -= amount
        self.solve_current_token()

        return self.current_token
    
    def parse(self):
        result = self.statements()
        token = self.current_token

        if not result.error and token.type != TT_EOF:
            return result.failure(InvalidSyntaxError(
                token.start_position,
                token.end_position,
                "Expected '+', '-', '*', '/' or '^'"
            ))

        return result
    
    ## Variables

    def variable(self):
        result = ParseResult()
        token = self.current_token
        scope_node = None

        if token.type == TT_OPEN_BRACKETS:
            result.register_advancement()
            self.advance()

            start_position = self.current_token_index
            scope_result = self.expression()
            scope_node = scope_result.node

            if scope_result.error:
                self.current_token_index = start_position
                self.solve_current_token()

                if self.current_token.matches(TT_KEYWORD, 'global'):
                    scope_node = GlobalScopeNode(self.current_token)

                    result.register_advancement()
                    self.advance()

                elif self.current_token.matches(TT_KEYWORD, 'default'):
                    scope_node = DefaultScopeNode(self.current_token)

                    result.register_advancement()
                    self.advance()

                else:
                    return result.failure(scope_result.error)

            token = self.current_token

            if token.type != TT_CLOSE_BRACKETS:
                return result.failure(ExpectedCharacterError(
                    token.start_position, token.end_position, ']'
                ))

            result.register_advancement()
            self.advance()

        token = self.current_token

        if token.type == TT_IDENTIFIER:
            result.register_advancement()
            self.advance()

            return result.success(VariableNode(TextNode(token), scope_node))
        
        elif token.type == TT_VARIABLE:
            result.register_advancement()
            self.advance()

            token = self.current_token

            if token.type in (TT_IDENTIFIER, TT_KEYWORD):
                result.register_advancement()
                self.advance()

                return result.success(VariableNode(TextNode(token), scope_node))

            baseAtom = result.register(self.baseAtom())
            if result.error: return result

            return result.success(VariableNode(baseAtom, scope_node))
        
        return result.failure(InvalidSyntaxError(
            token.start_position, token.end_position,
            "Expected identifier, '<' or '$'"
        ))

    def index(self):
        result = ParseResult()
        starting_token = self.current_token_index
        start_position = self.current_token.start_position

        variable = result.register(self.variable())
        if result.error: return result

        self.current_token_index = starting_token
        self.solve_current_token()

        atom = result.register(self.atom())
        if result.error: return result

        if not self.last_postfix_is_index:
            return result.failure(InvalidSyntaxError(
                start_position, self.current_token.end_position,
                "Indexing expected"
            ))

        return result.success((variable, atom))

    ## Binary Operations

    def baseAtom(self):
        result = ParseResult()
        token = self.current_token

        if token.type == TT_NUMBER:
            result.register_advancement()
            self.advance()

            return result.success(NumberNode(token))
        
        elif token.type == TT_TEXT:
            result.register_advancement()
            self.advance()

            return result.success(TextNode(token))

        elif token.type == TT_OPEN_PARENTHESIS:
            result.register_advancement()
            self.advance()

            expression = result.register(self.expression())

            if result.error: return result

            if self.current_token.type == TT_CLOSE_PARENTHESIS:
                result.register_advancement()
                self.advance()

                return result.success(expression)
            else:
                return result.failure(InvalidSyntaxError(
                    self.current_token.start_position,
                    self.current_token.end_position,
                    "Expected ')'"
                ))
                        
        start_position = self.current_token_index
        variable = self.variable()

        if not variable.error:
            return result.success(VariableAccessNode(variable.node))
        
        self.current_token_index = start_position
        self.solve_current_token()
        
        if token.type == TT_OPEN_BRACKETS:
            list_expression = result.register(self.list_expression())
            
            if result.error: return result
            return result.success(list_expression)
        
        elif token.type == TT_PIPE:
            dictionary_expression = result.register(self.dictionary_expression())

            if result.error: return result
            return result.success(dictionary_expression)
            
        return result.failure(InvalidSyntaxError(
            token.start_position, 
            token.end_position, 
            "Expected a number, a variable, '+', '-', '(' or '['"
        ))

    def atom(self):
        result = ParseResult()

        baseAtom = result.register(self.baseAtom())
        if result.error: return result

        currentNode = baseAtom

        while self.current_token.type in (TT_OPEN_PARENTHESIS, TT_OPEN_BRACKETS, TT_DOT):
            if self.current_token.type == TT_OPEN_PARENTHESIS:
                result.register_advancement()
                self.advance()

                argument_nodes = []

                if self.current_token.type == TT_CLOSE_PARENTHESIS:
                    result.register_advancement()
                    self.advance()
                else:
                    argument_nodes.append(result.register(self.expression()))

                    if result.error:
                        return result.failure(InvalidSyntaxError(
                            self.current_token.start_position, self.current_token.end_position,
                            "Expected ')', '$', number, identifier, '+', '-', '(' or '['"
                        ))
                    
                    while self.current_token.type == TT_COMMA:
                        result.register_advancement()
                        self.advance()

                        argument_nodes.append(result.register(self.expression()))
                        if result.error: return result

                    if self.current_token.type != TT_CLOSE_PARENTHESIS:
                        return result.failure(InvalidSyntaxError(
                            self.current_token.start_position, self.current_token.end_position,
                            "Expected ',' or ')'"
                        ))
                    
                    result.register_advancement()
                    self.advance()

                currentNode = CallNode(currentNode, argument_nodes)
                self.last_postfix_is_index = False

            if self.current_token.type == TT_OPEN_BRACKETS:
                result.register_advancement()
                self.advance()

                index = result.register(self.expression())
                if result.error: return result

                if self.current_token.type != TT_CLOSE_BRACKETS:
                    return result.failure(InvalidSyntaxError(
                        self.current_token.start_position, self.current_token.end_position,
                        "Expected ']'"
                    ))
                
                result.register_advancement()
                self.advance()
                
                currentNode = IndexingNode(currentNode, index)
                self.last_postfix_is_index = True

            if self.current_token.type == TT_DOT:
                result.register_advancement()
                self.advance()

                if not (self.current_token.type in (TT_IDENTIFIER, TT_KEYWORD)):
                    return result.failure(InvalidSyntaxError(
                        self.current_token.start_position, self.current_token.end_position,
                        "Expected identifier"
                    ))
                
                text_token = self.current_token
                
                result.register_advancement()
                self.advance()

                currentNode = IndexingNode(currentNode, TextNode(text_token), True)
                self.last_postfix_is_index = True

        return result.success(currentNode)

    def list_expression(self):
        result = ParseResult()
        element_nodes = []

        token = self.current_token
        start_position = token.start_position.copy()

        if token.type != TT_OPEN_BRACKETS:
            return result.failure(InvalidSyntaxError(
                start_position, self.current_token.end_position,
                "Expected '['"
            ))
        
        result.register_advancement()
        self.advance()

        while self.current_token.type == TT_NEW_LINE:
            result.register_advancement()
            self.advance()

        token = self.current_token

        if token.type == TT_CLOSE_BRACKETS:
            result.register_advancement()
            self.advance()
        else:
            element_nodes.append(result.register(self.expression()))

            if result.error:
                return result.failure(InvalidSyntaxError(
                    self.current_token.start_position, self.current_token.end_position,
                    "Expected ']', '$', number, identifier, '+', '-', or '('"
                ))
            
            while self.current_token.type == TT_NEW_LINE:
                result.register_advancement()
                self.advance()
            
            while self.current_token.type == TT_COMMA:
                result.register_advancement()
                self.advance()

                while self.current_token.type == TT_NEW_LINE:
                    result.register_advancement()
                    self.advance()

                element_nodes.append(result.register(self.expression()))
                if result.error: return result

                while self.current_token.type == TT_NEW_LINE:
                    result.register_advancement()
                    self.advance()

            if self.current_token.type != TT_CLOSE_BRACKETS:
                return result.failure(InvalidSyntaxError(
                    self.current_token.start_position, self.current_token.end_position,
                    "Expected ',' or ']'"
                ))
            
            result.register_advancement()
            self.advance()

        return result.success(ListNode(
            element_nodes,
            start_position,
            self.current_token.end_position.copy()
        ))

    def dictionary_element(self):
        result = ParseResult()

        while self.current_token.type == TT_NEW_LINE:
            result.register_advancement()
            self.advance()

        key = result.register(self.expression())

        if result.error:
            return result.failure(InvalidSyntaxError(
                self.current_token.start_position, self.current_token.end_position,
                "Expected ']', '$', number, identifier, '+', '-', or '('"
            ))

        while self.current_token.type == TT_NEW_LINE:
            result.register_advancement()
            self.advance()

        if self.current_token.type != TT_COLON:
            return result.failure(ExpectedCharacterError(
                self.current_token.start_position, self.current_token.end_position, ":"
            ))
        
        result.register_advancement()
        self.advance()

        while self.current_token.type == TT_NEW_LINE:
            result.register_advancement()
            self.advance()
        
        value = result.register(self.expression())
        return result.success((key, value))

    def dictionary_expression(self):
        result = ParseResult()
        node_dictionary = {}
    
        token = self.current_token
        start_position = token.start_position.copy()

        if token.type != TT_PIPE:
            return result.failure(InvalidSyntaxError(
                start_position, token.end_position,
                "Expected '|'"
            ))
        
        result.register_advancement()
        self.advance()

        while self.current_token.type == TT_NEW_LINE:
            result.register_advancement()
            self.advance()

        token = self.current_token

        if token.type == TT_PIPE:
            result.register_advancement()
            self.advance()
        else:
            (key, value) = result.register(self.dictionary_element())
            if result.error: return result

            node_dictionary[key] = value
            
            while self.current_token.type == TT_COMMA:
                result.register_advancement()
                self.advance()

                (key, value) = result.register(self.dictionary_element())
                if result.error: return result

                node_dictionary[key] = value

            while self.current_token.type == TT_NEW_LINE:
                result.register_advancement()
                self.advance()

            if self.current_token.type != TT_PIPE:
                return result.failure(InvalidSyntaxError(
                    self.current_token.start_position, self.current_token.end_position,
                    "Expected ',' or '|'"
                ))
            
            result.register_advancement()
            self.advance()

        return result.success(DictionaryNode(
            node_dictionary,
            start_position,
            self.current_token.end_position.copy()
        ))

    def power(self):
        return self.binary_operation(self.atom, (TT_POWER, ), self.factor)

    def factor(self):
        result = ParseResult()
        token = self.current_token

        if token.type in (TT_ADD, TT_SUBTRACT):
            result.register_advancement()
            self.advance()

            factor = result.register(self.factor())

            if result.error: return result            
            return result.success(UnaryOperationNode(token, factor))
        
        return self.power()

    def term(self):
        return self.binary_operation(self.factor, (TT_MULIPLY, TT_DIVIDE))
    
    def if_expression(self):
        result = ParseResult()

        if not self.current_token.matches(TT_KEYWORD, 'if'):
            return result.failure(InvalidSyntaxError(
                self.current_token.start_position, self.current_token.end_position,
                "Expected 'if'"
            ))
        
        result.register_advancement()
        self.advance()

        while self.current_token.type == TT_NEW_LINE:
            result.register_advancement()
            self.advance()

        if not self.current_token.type == TT_OPEN_PARENTHESIS:
            return result.failure(ExpectedCharacterError(
                self.current_token.start_position, self.current_token.end_position, '('
            ))
        
        result.register_advancement()
        self.advance()

        while self.current_token.type == TT_NEW_LINE:
            result.register_advancement()
            self.advance()
        
        expression = result.register(self.expression())
        if result.error: return result

        while self.current_token.type == TT_NEW_LINE:
            result.register_advancement()
            self.advance()

        if not self.current_token.type == TT_CLOSE_PARENTHESIS:
            return result.failure(ExpectedCharacterError(
                self.current_token.start_position, self.current_token.end_position, ')'
            ))

        result.register_advancement()
        self.advance()

        while self.current_token.type == TT_NEW_LINE:
            result.register_advancement()
            self.advance()

        atom = result.register(self.atom())
        if result.error: return result

        position_before_new_line = self.current_token_index

        while self.current_token.type == TT_NEW_LINE:
            result.register_advancement()
            self.advance()
        
        if self.current_token.matches(TT_KEYWORD, "else"):
            result.register_advancement()
            self.advance()

            while self.current_token.type == TT_NEW_LINE:
                result.register_advancement()
                self.advance()

            start_position = self.current_token_index
            if_expression = self.if_expression()
            
            if if_expression.error:
                self.current_token_index = start_position
                self.solve_current_token()

                else_atom = result.register(self.atom())
                if result.error: return result

                else_node = else_atom

            else: else_node = result.register(if_expression)

            return result.success(IfNode(expression, atom, else_node))
        
        else:
            self.current_token_index = position_before_new_line
            self.solve_current_token()
        
        return result.success(IfNode(expression, atom))
    
    def while_expression(self):
        result = ParseResult()

        if not self.current_token.matches(TT_KEYWORD, 'while'):
            return result.failure(InvalidSyntaxError(
                self.current_token.start_position, self.current_token.end_position,
                "Expected 'while'"
            ))
        
        result.register_advancement()
        self.advance()

        while self.current_token.type == TT_NEW_LINE:
            result.register_advancement()
            self.advance()

        if not self.current_token.type == TT_OPEN_PARENTHESIS:
            return result.failure(ExpectedCharacterError(
                self.current_token.start_position, self.current_token.end_position, '('
            ))
        
        result.register_advancement()
        self.advance()

        while self.current_token.type == TT_NEW_LINE:
            result.register_advancement()
            self.advance()
        
        expression = result.register(self.expression())
        if result.error: return result

        while self.current_token.type == TT_NEW_LINE:
            result.register_advancement()
            self.advance()

        if not self.current_token.type == TT_CLOSE_PARENTHESIS:
            return result.failure(ExpectedCharacterError(
                self.current_token.start_position, self.current_token.end_position, ')'
            ))

        result.register_advancement()
        self.advance()

        while self.current_token.type == TT_NEW_LINE:
            result.register_advancement()
            self.advance()

        atom = result.register(self.atom())
        if result.error: return result
        
        return result.success(WhileNode(expression, atom))
        
    def arithmetic_expression(self):
        return self.binary_operation(self.term, (TT_ADD, TT_SUBTRACT))
    
    def comparaison_expression(self):
        result = ParseResult()
        token = self.current_token

        if token.matches(TT_KEYWORD, 'not'):
            operation_token = self.current_token
            
            result.register_advancement()
            self.advance()

            node = result.register(self.comparaison_expression())

            if result.error: return result
            return result.success(UnaryOperationNode(operation_token, node))
        
        node = result.register(self.binary_operation(self.arithmetic_expression, COMPARAISON_TOKEN_TYPES))
        token = self.current_token

        if result.error:
            return result.failure(InvalidSyntaxError(
                token.start_position, token.end_position,
                "Expected a number, a variable, '+', '-', '(', '[' or 'not'"
            ))
        
        return result.success(node)

    def expression(self):
        result = ParseResult()

        if self.current_token.matches(TT_KEYWORD, 'if'):
            return self.if_expression()
        
        if self.current_token.matches(TT_KEYWORD, 'while'):
            return self.while_expression()

        starting_index = self.current_token_index
        variable = self.variable()

        if not variable.error:
            token = self.current_token

            if token.type == TT_EQUALS:
                result.register_advancement()
                self.advance()

                expression = result.register(self.expression())

                if result.error: return result
                return result.success(VariableAssignmentNode(variable.node, expression))
        
        self.current_token_index = starting_index
        self.solve_current_token()

        starting_index = self.current_token_index
        index = self.index()

        if not index.error:
            (variable, atom) = result.register(index)
            token = self.current_token

            if token.type == TT_EQUALS:
                result.register_advancement()
                self.advance()

                expression = result.register(self.expression())

                if result.error: return result
                return result.success(IndexAssignmentNode(variable, atom, expression))

        self.current_token_index = starting_index
        self.solve_current_token()

        node = result.register(self.binary_operation(self.comparaison_expression, ((TT_KEYWORD, 'and'), (TT_KEYWORD, 'or'))))

        if result.error: 
            return result.failure(InvalidSyntaxError(
                self.current_token.start_position, self.current_token.end_position,
                "Expected '$', number, identifier, '+', '-', '(' or '['"
            ))
        
        return result.success(node)
    
    def statements(self):
        result = ParseResult()
        statements = []

        start_position = self.current_token.start_position.copy()

        while self.current_token.type == TT_NEW_LINE:
            result.register_advancement()
            self.advance()

        if self.current_token.type == TT_EOF:
            return result.success(ListNode(
                [NullNode(self.current_token.start_position, self.current_token.end_position)],
                self.current_token.start_position, self.current_token.end_position
            ))

        statement = result.register(self.expression())
        if result.error: return result

        statements.append(statement)

        more_statements = True

        while True:
            new_line_count = 0

            while self.current_token.type == TT_NEW_LINE:
                result.register_advancement()
                self.advance()

                new_line_count += 1

            if new_line_count == 0:
                more_statements = False

            if not more_statements: break

            statement = result.try_register(self.expression())

            if not statement:
                self.reverse(result.to_reverse_count)

                more_statements = False
                continue

            statements.append(statement)

        return result.success(ListNode(
            statements,
            start_position,
            self.current_token.start_position.copy()
        ))
    
    def binary_operation(self, left_function, operation_tokens: tuple, right_function = None):
        result = ParseResult()
        left = result.register(left_function())

        if result.error: return result

        while (self.current_token.type in operation_tokens) or (self.current_token.type, self.current_token.value) in operation_tokens:
            token = self.current_token
            result.register_advancement()
            self.advance()


            right = result.register(right_function() if right_function else left_function())
            if result.error: return result

            left = BinaryOperationNode(left, token, right) # type: ignore

        return result.success(left)

#endregion


#region RUNTIME RESULT

class RuntimeResult:
    def __init__(self):
        self.value = None
        self.error = None

    def register(self, result):
        if result.error: self.error = result.error
        return result.value
    
    def success(self, value):
        self.value = value
        return self
    
    def failure(self, error):
        self.error = error
        return self

#endregion

#region VALUES

def get_value_type_from_object(object) -> type:
    if isinstance(object, str):
        return Text
    elif isinstance(object, (float, int)):
        return Number
    elif isinstance(object, list):
        return List
    elif isinstance(object, (FunctionType, BuiltinFunctionType)):
        return BuiltIn
    else:
        return Null

def get_value_name_from_object(object) -> str:
    return get_value_type_from_object(object).__name__

def get_value_from_object(object):
    return get_value_type_from_object(object)(object)

def get_object_type_from_value(value) -> type:
    if isinstance(value, Text):
        return str
    elif isinstance(value, Number):
        return float
    elif isinstance(value, List):
        return list
    elif isinstance(value, BuiltIn):
        return FunctionType
    else:
        return Null    

def get_object_from_value(value):
    if isinstance(value, (Number, Text, BuiltIn, List)):
        return value.value
    else:
        return None


class Value(ABC):
    def __init__(self, value):
        self.value = value
        self.set_position()
        self.set_context()

    def set_position(self, start_position = None, end_position = None):
        self.start_position = start_position
        self.end_position = end_position

        return self
    
    def set_context(self, context = None):
        self.context = context
        return self
    
    @abstractmethod
    def copy(self):
        pass

    ## Execute

    @abstractmethod
    def execute(self, arguments: list[object]) -> RuntimeResult:
        pass

    ## Index

    @abstractmethod
    def index(self, other) -> RuntimeResult:
        pass

    @abstractmethod
    def assign_index(self, index, value) -> RuntimeResult:
        pass
    
    ## Binary Operations

    @abstractmethod
    def added_to(self, other) -> RuntimeResult:
        pass
    
    @abstractmethod
    def subtracted_by(self, other) -> RuntimeResult:
        pass

    @abstractmethod
    def multiplied_by(self, other) -> RuntimeResult:
        pass

    @abstractmethod
    def divided_by(self, other) -> RuntimeResult:
        pass

    @abstractmethod
    def powered_by(self, other) -> RuntimeResult:
        pass

    ## Comparaisons

    @abstractmethod
    def is_equals_to(self, other) -> RuntimeResult:
        pass
    
    @abstractmethod
    def is_not_equals_to(self, other) -> RuntimeResult:
        result = RuntimeResult()

        is_equals = result.register(self.is_equals_to(other))
        if result.error: return result

        is_not_equals = result.register(is_equals.not_())
        if result.error: return result

        return result.success(is_not_equals)

    @abstractmethod
    def is_greater_than(self, other) -> RuntimeResult:
        pass

    @abstractmethod
    def is_less_than(self, other) -> RuntimeResult:
        pass

    @abstractmethod
    def is_greater_or_equals(self, other) -> RuntimeResult:
        result = RuntimeResult()

        is_greater = result.register(self.is_greater_than(other))
        if result.error: return result

        is_equals = result.register(self.is_equals_to(other))
        if result.error: return result      

        is_greater_or_equals = result.register(is_greater.or_(is_equals))
        if result.error: return result

        return result.success(is_greater_or_equals)

    @abstractmethod
    def is_less_or_equals(self, other) -> RuntimeResult:
        result = RuntimeResult()

        is_less = result.register(self.is_less_than(other))
        if result.error: return result

        is_equals = result.register(self.is_equals_to(other))
        if result.error: return result      

        is_less_or_equals = result.register(is_less.or_(is_equals))
        if result.error: return result

        return result.success(is_less_or_equals)

    ## Logical operators

    @abstractmethod
    def and_(self, other) -> RuntimeResult:
        result = RuntimeResult()

        self_boolean = result.register(self.to_boolean())
        if result.error: return result

        other_boolean = result.register(other.to_boolean())
        if result.error: return result

        if self_boolean.value and other_boolean.value:
            return result.success(Number(1))
        else:
            return result.success(Number(0))
    
    @abstractmethod
    def or_(self, other) -> RuntimeResult:
        result = RuntimeResult()

        self_boolean = result.register(self.to_boolean())
        if result.error: return result

        other_boolean = result.register(other.to_boolean())
        if result.error: return result

        if self_boolean.value or other_boolean.value:
            return result.success(Number(1))
        else:
            return result.success(Number(0))

    @abstractmethod
    def not_(self) -> RuntimeResult:
        result = RuntimeResult()

        boolean = result.register(self.to_boolean())
        if result.error: return result

        if boolean.value == 1:
            return result.success(Number(0))
        else:
            return result.success(Number(1))

    ## Conversion

    @abstractmethod
    def to_boolean(self) -> RuntimeResult:
        pass

    @abstractmethod
    def to_number(self) -> RuntimeResult:
        pass

    @abstractmethod
    def to_text(self) -> RuntimeResult:
        pass

    @abstractmethod
    def to_list(self) -> RuntimeResult:
        pass

    @abstractmethod
    def to_built_in(self) -> RuntimeResult:
        pass


class Number(Value):
    def __init__(self, value: float):
        super().__init__(float(value))

    def set_position(self, start_position = None, end_position = None):
        return super().set_position(start_position, end_position)
    
    def set_context(self, context=None):
        return super().set_context(context)
    
    def copy(self):
        copy = Number(self.value)
        copy.set_position(self.start_position, self.end_position)
        copy.set_context(self.context)

        return copy
    
    def __str__(self) -> str:
        return str(int(self.value)) if self.value.is_integer() else str(self.value)
    
    def __repr__(self) -> str:
        return str(self)
    
    ## Execute

    def execute(self, arguments: list[Value]) -> RuntimeResult:
        return RuntimeResult().failure(RuntimeError(
            self.start_position, self.end_position,
            f"An object of type {__class__.__name__} can't be executed",
            self.context
        ))
    
    ## Index

    def index(self, other: Value) -> RuntimeResult:
        return RuntimeResult().failure(RuntimeError(
            self.start_position, other.end_position.copy().advance(),
            f"An object of type {__class__.__name__} can't be indexed",
            self.context
        ))
    
    def assign_index(self, index: Value, value: Value) -> RuntimeResult:
        return RuntimeResult().failure(RuntimeError(
            self.start_position, index.end_position.copy().advance(),
            f"An object of type {__class__.__name__} does not support index assignment",
            self.context
        ))
    
    ## Binary Operations

    def added_to(self, other: Value) -> RuntimeResult:
        result = RuntimeResult()

        if isinstance(other, Number):
            return result.success(Number(self.value + other.value)
                .set_context(self.context)
                .set_position(self.start_position, other.end_position))
        elif isinstance(other, Text):
            return result.success(Text(str(self) + other.value)
                .set_context(self.context)\
                .set_position(self.start_position, other.end_position))
        
        return result.failure(RuntimeError(
            self.start_position, other.end_position,
            f"An object of type {__class__.__name__} can't be added to an object of type {type(other).__name__}",
            self.context
        ))
        
    def subtracted_by(self, other: Value) -> RuntimeResult:
        result = RuntimeResult()

        if isinstance(other, Number):
            return result.success(Number(self.value - other.value)
                .set_context(self.context)\
                .set_position(self.start_position, other.end_position))

        return result.failure(RuntimeError(
            self.start_position, other.end_position,
            f"An object of type {__class__.__name__} can't be subtracted by an object of type {type(other).__name__}",
            self.context
        ))
        
    def multiplied_by(self, other: Value) -> RuntimeResult:
        result = RuntimeResult()

        if isinstance(other, Number):
            return result.success(Number(self.value * other.value)
                .set_context(self.context)\
                .set_position(self.start_position, other.end_position))

        return result.failure(RuntimeError(
            self.start_position, other.end_position,
            f"An object of type {__class__.__name__} can't be multiplied by an object of type {type(other).__name__}",
            self.context
        ))
        
    def divided_by(self, other: Value) -> RuntimeResult:
        result = RuntimeResult()

        if isinstance(other, Number):
            if other.value == 0:
                return result.failure(RuntimeError(
                    self.start_position,
                    other.end_position,
                    'Attempted to divide by zero',
                    self.context
                ))
            
            return result.success(Number(self.value / other.value)
                .set_context(self.context)\
                .set_position(self.start_position, other.end_position))

        return result.failure(RuntimeError(
            self.start_position, other.end_position,
            f"An object of type {__class__.__name__} can't be divided by an object of type {type(other).__name__}",
            self.context
        ))

    def powered_by(self, other: Value) -> RuntimeResult:
        result = RuntimeResult()

        if isinstance(other, Number):
            return result.success(Number(self.value ** other.value)
                .set_context(self.context)\
                .set_position(self.start_position, other.end_position))

        return result.failure(RuntimeError(
            self.start_position, other.end_position,
            f"An object of type {__class__.__name__} can't be raised to the power of an object of type {type(other).__name__}",
            self.context
        ))
    
    ## Comparaisons

    def is_equals_to(self, other) -> RuntimeResult:
        result = RuntimeResult()

        if isinstance(other, Number):
            return result.success(Number(self.value == other.value)
                .set_context(self.context)\
                .set_position(self.start_position, other.end_position))

        return result.success(Number(0)
            .set_context(self.context)\
            .set_position(self.start_position, other.end_position))
    
    def is_not_equals_to(self, other) -> RuntimeResult:
        return super().is_not_equals_to(other)

    def is_greater_than(self, other) -> RuntimeResult:
        result = RuntimeResult()

        if isinstance(other, Number):
            return result.success(Number(self.value > other.value)
                .set_context(self.context)\
                .set_position(self.start_position, other.end_position))

        return result.failure(RuntimeError(
            self.start_position, other.end_position,
            f"An object of type {__class__.__name__} can't be compared with an object of type {type(other).__name__} with a '>' or '>=' operator",
            self.context
        ))

    def is_less_than(self, other) -> RuntimeResult:
        result = RuntimeResult()

        if isinstance(other, Number):
            return result.success(Number(self.value < other.value)
                .set_context(self.context)\
                .set_position(self.start_position, other.end_position))

        return result.failure(RuntimeError(
            self.start_position, other.end_position,
            f"An object of type {__class__.__name__} can't be compared with an object of type {type(other).__name__} with a '<' or '<=' operator",
            self.context
        ))

    def is_greater_or_equals(self, other) -> RuntimeResult:
        return super().is_greater_or_equals(other)

    def is_less_or_equals(self, other) -> RuntimeResult:
        return super().is_less_or_equals(other)
    
    ## Logical operators

    def and_(self, other) -> RuntimeResult:
        return super().and_(other)
    
    def or_(self, other) -> RuntimeResult:
        return super().or_(other)
    
    def not_(self) -> RuntimeResult:
        return super().not_()
        
    ## Conversion

    def to_boolean(self) -> RuntimeResult:
        result = RuntimeResult()

        if self.value > 0:
            return result.success(Number(1))
        else:
            return result.success(Number(0))
        
    def to_number(self) -> RuntimeResult:
        return RuntimeResult().success(self)

    def to_text(self) -> RuntimeResult:
        return RuntimeResult().success(Text(str(self)))

    def to_list(self) -> RuntimeResult:
        return RuntimeResult().success(List([self]))

    def to_built_in(self) -> RuntimeResult:
        return RuntimeResult().failure(RuntimeError(
            self.start_position, self.end_position,
            f"An object of type {__class__.__name__} can't be casted to a built-in",
            self.context
        ))


class Text(Value):
    def __init__(self, value: str):
        super().__init__(value)
        self.base_value = None

    def set_position(self, start_position = None, end_position = None):
        return super().set_position(start_position, end_position)
    
    def set_context(self, context = None):
        return super().set_context(context)
    
    def copy(self):
        copy = Text(self.value)
        copy.base_value = self.base_value
        copy.set_position(self.start_position, self.end_position)
        copy.set_context(self.context)

        return copy
    
    def __str__(self) -> str:
        return self.value
    
    def __repr__(self) -> str:
        return f'"{self.value}"'
    
    ## Execute
    def execute(self, arguments: list[Value]) -> RuntimeResult:
        result = RuntimeResult()

        if self.base_value is not None:
            arguments.insert(0, self.base_value)

        new_context = Context('Text', self.context, self.start_position)
        new_context.symbol_table = SymbolTable(new_context.parent.symbol_table)

        argument_list = List(arguments).set_context(new_context)
        new_context.symbol_table.set(Text("arguments"), argument_list)
            
        value, error = run('Text', self.value, new_context)

        if error:
            return result.failure(error)

        return_value = value.value[len(value.value) - 1]
        return result.success(return_value)

    ## Index
    def index(self, other: Value) -> RuntimeResult:
        result = RuntimeResult()

        if isinstance(other, Number):
            if other.value < 0:
                return result.failure(RuntimeError(
                    self.start_position, other.end_position.copy().advance(),
                    f"An object of type {__class__.__name__} can't be indexed by a negative number",
                    self.context
                ))

            if not other.value.is_integer():
                return result.failure(RuntimeError(
                    self.start_position, other.end_position.copy().advance(),
                    f"An object of type {__class__.__name__} can't be indexed by a decimal number",
                    self.context
                ))

            return result.success(Text(self.value[int(other.value)])
                .set_context(self.context)
                .set_position(self.start_position, other.end_position))

        return result.failure(RuntimeError(
            self.start_position, other.end_position.copy().advance(),
            f"An object of type {__class__.__name__} can't be indexed with an object of type {type(other).__name__}",
            self.context
        ))
    
    ## Index
    def index(self, other: Value) -> RuntimeResult:
        result = RuntimeResult()

        if isinstance(other, Number):
            if other.value < 0:
                return result.failure(RuntimeError(
                    self.start_position, other.end_position.copy().advance(),
                    f"An object of type {__class__.__name__} can't be indexed by a negative number",
                    self.context
                ))

            if not other.value.is_integer():
                return result.failure(RuntimeError(
                    self.start_position, other.end_position.copy().advance(),
                    f"An object of type {__class__.__name__} can't be indexed by a decimal number",
                    self.context
                ))

            return result.success(Text(self.value[int(other.value)])
                .set_context(self.context)
                .set_position(self.start_position, other.end_position))

        return result.failure(RuntimeError(
            self.start_position, other.end_position.copy().advance(),
            f"An object of type {__class__.__name__} can't be indexed with an object of type {type(other).__name__}",
            self.context
        ))
    
    ## Index
    def assign_index(self, index: Value, value: Value) -> RuntimeResult:
        return RuntimeResult().failure(RuntimeError(
            self.start_position, index.end_position.copy().advance(),
            f"An object of type {__class__.__name__} does not support index assignment",
            self.context
        ))
    
    ## Binary Operations
    def added_to(self, other: Value) -> RuntimeResult:
        result = RuntimeResult()

        if isinstance(other, Text):
            return result.success(Text(self.value + other.value)
                .set_context(self.context)
                .set_position(self.start_position, other.end_position))
        elif not isinstance(other, BuiltIn):
            return result.success(Text(self.value + str(other))
                .set_context(self.context)
                .set_position(self.start_position, other.end_position))

        return result.failure(RuntimeError(
            self.start_position, other.end_position,
            f"An object of type {__class__.__name__} can't be added to an object of type {type(other).__name__}",
            self.context
        ))
        
    def subtracted_by(self, other: Value) -> RuntimeResult:
        result = RuntimeResult()

        if isinstance(other, Text):
            return result.success(Text(self.value.removesuffix(other.value))
                .set_context(self.context)
                .set_position(self.start_position, other.end_position))

        return result.failure(RuntimeError(
            self.start_position, other.end_position,
            f"An object of type {__class__.__name__} can't be subtracted by an object of type {type(other).__name__}",
            self.context
        ))
        
    def multiplied_by(self, other: Value) -> RuntimeResult:
        result = RuntimeResult()

        if isinstance(other, Number):
            if other.value < 0:
                return result.failure(RuntimeError(
                    self.start_position, other.end_position.copy().advance(),
                    f"An object of type {__class__.__name__} can't be multiplied by a negative number",
                    self.context
                ))

            if not other.value.is_integer():
                return result.failure(RuntimeError(
                    self.start_position, other.end_position.copy().advance(),
                    f"An object of type {__class__.__name__} can't be multiplied by a decimal number",
                    self.context
                ))

            return result.success(Text(self.value * int(other.value))
                .set_context(self.context)
                .set_position(self.start_position, other.end_position))

        return result.failure(RuntimeError(
            self.start_position, other.end_position,
            f"An object of type {__class__.__name__} can't be multiplied by an object of type {type(other).__name__}",
            self.context
        ))
        
    def divided_by(self, other: Value) -> RuntimeResult:
        return RuntimeResult().failure(RuntimeError(
            self.start_position, other.end_position,
            f"An object of type {__class__.__name__} can't be divided",
            self.context
        ))

    def powered_by(self, other: Value) -> RuntimeResult:
        return RuntimeResult().failure(RuntimeError(
            self.start_position, other.end_position,
            f"An object of type {__class__.__name__} can't be raised to a power",
            self.context
        ))
    
    ## Comparisons
    def is_equals_to(self, other) -> RuntimeResult:
        result = RuntimeResult()

        if isinstance(other, Text):
            return result.success(Number(self.value == other.value)
                .set_context(self.context)
                .set_position(self.start_position, other.end_position))

        return result.success(Number(0)
            .set_context(self.context)
            .set_position(self.start_position, other.end_position))
    
    def is_not_equals_to(self, other) -> RuntimeResult:
        return super().is_not_equals_to(other)

    def is_greater_than(self, other) -> RuntimeResult:
        result = RuntimeResult()

        if isinstance(other, Text):
            return result.success(Number(len(self.value) > len(other.value))
                .set_context(self.context)
                .set_position(self.start_position, other.end_position))

        return result.failure(RuntimeError(
            self.start_position, other.end_position,
            f"An object of type {__class__.__name__} can't be compared with an object of type {type(other).__name__} using '>' or '>='",
            self.context
        ))

    def is_less_than(self, other) -> RuntimeResult:
        result = RuntimeResult()

        if isinstance(other, Text):
            return result.success(Number(len(self.value) < len(other.value))
                .set_context(self.context)
                .set_position(self.start_position, other.end_position))

        return result.failure(RuntimeError(
            self.start_position, other.end_position,
            f"An object of type {__class__.__name__} can't be compared with an object of type {type(other).__name__} using '<' or '<='",
            self.context
        ))

    def is_greater_or_equals(self, other) -> RuntimeResult:
        return super().is_greater_or_equals(other)

    def is_less_or_equals(self, other) -> RuntimeResult:
        return super().is_less_or_equals(other)
    
    ## Logical operators
    def and_(self, other) -> RuntimeResult:
        return super().and_(other)
    
    def or_(self, other) -> RuntimeResult:
        return super().or_(other)
    
    def not_(self) -> RuntimeResult:
        return super().not_()
    
    ## Conversion
    def to_boolean(self) -> RuntimeResult:
        return RuntimeResult().success(Number(not (self.value.strip() == '')))
    
    def to_number(self) -> RuntimeResult:
        result = RuntimeResult()

        try:
            return result.success(Number(float(self.value)))
        except:
            return result.failure(RuntimeError(
                self.start_position, self.end_position,
                f"Text object {repr(self)} can't be casted to a number",
                self.context
            ))

    def to_text(self) -> RuntimeResult:
        return RuntimeResult().success(self)

    def to_list(self) -> RuntimeResult:
        return RuntimeResult().success(List([self]))

    def to_built_in(self) -> RuntimeResult:
        result = RuntimeResult()
        
        try:
            return result.success(BuiltIn(built_ins[self.value]))
        except:
            return result.failure(RuntimeError(
                self.start_position, self.end_position,
                f"Text object {repr(self)} can't be casted to a built-in",
                self.context
            ))


class List(Value):
    def __init__(self, value: list):
        super().__init__(value)

    def set_position(self, start_position = None, end_position = None):
        return super().set_position(start_position, end_position)
    
    def set_context(self, context=None):
        return super().set_context(context)
    
    def copy(self):
        copy = List(self.value[:])
        copy.set_position(self.start_position, self.end_position)
        copy.set_context(self.context)

        return copy
    
    def __str__(self) -> str:
        return f"[{', '.join(str(x) for x in self.value)}]"
    
    def __repr__(self) -> str:
        return f"[{', '.join(repr(x) for x in self.value)}]"
    
    ## Execute

    def execute(self, arguments: list[Value]) -> RuntimeResult:
        return RuntimeResult().failure(RuntimeError(
            self.start_position, self.end_position,
            f"An object of type {__class__.__name__} can't be executed",
            self.context
        ))
    
    ## Index

    def index(self, other: Value) -> RuntimeResult:
        result = RuntimeResult()

        if isinstance(other, Number):
            if other.value < 0:
                return result.failure(RuntimeError(
                    self.start_position, other.end_position.copy().advance(),
                    f"An object of type {__class__.__name__} can't be indexed by a negative number",
                    self.context
                ))

            if not other.value.is_integer():
                return result.failure(RuntimeError(
                    self.start_position, other.end_position.copy().advance(),
                    f"An object of type {__class__.__name__} can't be indexed by a decimal number",
                    self.context
                ))
            
            if other.value >= len(self.value):
                return result.failure(RuntimeError(
                    self.start_position, other.end_position.copy().advance(),
                    f"Index is out of range",
                    self.context
                ))

            return result.success(self.value[int(other.value)]
                .set_context(self.context)
                .set_position(self.start_position, other.end_position))

        return result.failure(RuntimeError(
            self.start_position, other.end_position.copy().advance(),
            f"An object of type {__class__.__name__} can't be indexed with an object of type {type(other).__name__}",
            self.context
        ))
    
    def assign_index(self, index: Value, value: Value):
        result = RuntimeResult()

        if isinstance(index, Number):
            if index.value < 0:
                return result.failure(RuntimeError(
                    self.start_position, index.end_position.copy().advance(),
                    f"An object of type {__class__.__name__} can't be indexed by a negative number",
                    self.context
                ))

            if not index.value.is_integer():
                return result.failure(RuntimeError(
                    self.start_position, index.end_position.copy().advance(),
                    f"An object of type {__class__.__name__} can't be indexed by a decimal number",
                    self.context
                ))
            
            if index.value >= len(self.value):
                return result.failure(RuntimeError(
                    self.start_position, index.end_position.copy().advance(),
                    f"Index is out of range",
                    self.context
                ))
            
            self.value[int(index.value)] = value

            return result.success(self.copy()
                .set_context(self.context)
                .set_position(self.start_position, index.end_position))

        return result.failure(RuntimeError(
            self.start_position, index.end_position.copy().advance(),
            f"An object of type {__class__.__name__} can't be indexed with an object of type {type(index).__name__}",
            self.context
        ))

    ## Binary Operations

    def added_to(self, other: Value) -> RuntimeResult:
        if isinstance(other, List):
            new_list = self.copy()
            new_list.value = new_list.value + other.value

            return RuntimeResult().success(new_list)
        elif isinstance(other, Text):
            return RuntimeResult().success(Text(str(self) + other.value))

        return RuntimeResult().failure(RuntimeError(
            self.start_position, other.end_position,
            f"An object of type {__class__.__name__} can't be added to an object of type {other.__class__.__name__}",
            self.context
        ))
        
    def subtracted_by(self, other: Value) -> RuntimeResult:
        return RuntimeResult().failure(RuntimeError(
            self.start_position, other.end_position,
            f"An object of type {__class__.__name__} can't be subtracted to",
            self.context
        ))
        
    def multiplied_by(self, other: Value) -> RuntimeResult:
        result = RuntimeResult()

        if isinstance(other, Number):
            if other.value < 0:
                return result.failure(RuntimeError(
                    self.start_position, other.end_position,
                    f"An object of type {__class__.__name__} can't be multiplied by a negative number",
                    self.context
                ))

            if not other.value.is_integer():
                return result.failure(RuntimeError(
                    self.start_position, other.end_position,
                    f"An object of type {__class__.__name__} can't be multiplied by a decimal number",
                    self.context
                ))
            
            new_list = List([])\
                .set_position(self.start_position, self.end_position)\
                .set_context(self.context)
            
            for i in range(int(other.value)):
                new_list.value.extend(self.value)

            return result.success(new_list)

        return result.failure(RuntimeError(
            self.start_position, other.end_position,
            f"An object of type {__class__.__name__} can't be multiplied by an object of type {type(other).__name__}",
            self.context
        ))
        
    def divided_by(self, other: Value) -> RuntimeResult:
        return RuntimeResult().failure(RuntimeError(
            self.start_position, other.end_position,
            f"An object of type {__class__.__name__} can't be divided by an object of type {type(other).__name__}",
            self.context
        ))

    def powered_by(self, other: Value) -> RuntimeResult:
        return RuntimeResult().failure(RuntimeError(
            self.start_position, other.end_position,
            f"An object of type {__class__.__name__} can't be raised to the power of an object of type {type(other).__name__}",
            self.context
        ))
    
    ## Comparaisons

    def is_equals_to(self, other) -> RuntimeResult:
        result = RuntimeResult()

        if isinstance(other, List):
            return result.success(Number(self.value == other.value)
                .set_context(self.context)
                .set_position(self.start_position, other.end_position))

        return result.success(Number(0)
            .set_context(self.context)
            .set_position(self.start_position, other.end_position))
    
    def is_not_equals_to(self, other) -> RuntimeResult:
        return super().is_not_equals_to(other)

    def is_greater_than(self, other) -> RuntimeResult:
        result = RuntimeResult()

        if isinstance(other, List):
            return result.success(Number(len(self.value) > len(other.value))\
                .set_context(self.context)\
                .set_position(self.start_position, other.end_position))

        return result.failure(RuntimeError(
            self.start_position, other.end_position,
            f"An object of type {__class__.__name__} can't be compared with an object of type {type(other).__name__} with a '>' or '>=' operator",
            self.context
        ))

    def is_less_than(self, other) -> RuntimeResult:
        result = RuntimeResult()

        if isinstance(other, List):
            return result.success(Number(len(self.value) < len(other.value))\
                .set_context(self.context)\
                .set_position(self.start_position, other.end_position))

        return result.failure(RuntimeError(
            self.start_position, other.end_position,
            f"An object of type {__class__.__name__} can't be compared with an object of type {type(other).__name__} with a '>' or '>=' operator",
            self.context
        ))

    def is_greater_or_equals(self, other) -> RuntimeResult:
        return super().is_greater_or_equals(other)

    def is_less_or_equals(self, other) -> RuntimeResult:
        return super().is_less_or_equals(other)
    
    ## Logical operators

    def and_(self, other) -> RuntimeResult:
        return super().and_(other)
    
    def or_(self, other) -> RuntimeResult:
        return super().or_(other)
    
    def not_(self) -> RuntimeResult:
        return super().not_()
    
    ## Conversion

    def to_boolean(self) ->  RuntimeResult:
        return RuntimeResult().success(Number(len(self.value) > 0))
    
    def to_number(self) ->  RuntimeResult:
        return RuntimeResult().success(Number(len(self.value)))

    def to_text(self) ->  RuntimeResult:
        return RuntimeResult().success(Text(repr(self)))

    def to_list(self) ->  RuntimeResult:
        return RuntimeResult().success(self)

    def to_built_in(self) ->  RuntimeResult:
        return RuntimeResult().failure(RuntimeError(
            self.start_position, self.end_position,
            f"An object of type {__class__.__name__} can't be casted to a built-in",
            self.context
        ))


class Dictionary(Value):
    def __init__(self, value: dict):
        super().__init__(value)

    def set_position(self, start_position = None, end_position = None):
        return super().set_position(start_position, end_position)
    
    def set_context(self, context=None):
        return super().set_context(context)
    
    def copy(self):
        copy = Dictionary(self.value.copy())
        copy.set_position(self.start_position, self.end_position)
        copy.set_context(self.context)

        return copy
    
    def __str__(self) -> str:
        return f'|{str(self.value).removeprefix("{").removesuffix("}")}|'
    
    def __repr__(self) -> str:
        return f'|{repr(self.value).removeprefix("{").removesuffix("}")}|'
    
    ## Execute

    def execute(self, arguments: list[Value]) -> RuntimeResult:
        return RuntimeResult().failure(RuntimeError(
            self.start_position, self.end_position,
            f"An object of type {__class__.__name__} can't be executed",
            self.context
        ))
    
    ## Index

    def index(self, other: Value) -> RuntimeResult:
        result = RuntimeResult()

        keys = map(lambda e: e.value, list(self.value.keys()))
        values = list(self.value.values())
        dictionary = dict(zip(keys, values))

        if other.value in dictionary:
            return result.success(dictionary[other.value]
                .set_context(self.context)
                .set_position(self.start_position, other.end_position))

        return result.failure(RuntimeError(
            self.start_position, other.end_position.copy().advance(),
            f"Key not found: {str(other)}",
            self.context
        ))
    
    def assign_index(self, index: Value, value: Value) -> RuntimeResult:
        result = RuntimeResult()

        for k, v in self.value.items():
            if k.value == index.value:
                self.value[k] = value

                return result.success(self.copy()
                    .set_context(self.context)
                    .set_position(self.start_position, index.end_position))
        
        self.value[index] = value

        return result.success(self.copy()
            .set_context(self.context)
            .set_position(self.start_position, index.end_position))

    ## Binary Operations

    def added_to(self, other: Value) -> RuntimeResult:
        result = RuntimeResult()
        
        if isinstance(other, Dictionary):
            new_dictionary = self.copy()
            new_dictionary.value.update(other.value)

            return result.success(new_dictionary)
        elif isinstance(other, Text):
            return RuntimeResult().success(Text(str(self) + other.value))
        else:
            return result.failure(RuntimeError(
                self.start_position, other.end_position.copy(),
                f"An object of type {__class__.__name__} can't be added to an object of type {type(other).__name__}",
                self.context
            ))

    def subtracted_by(self, other: Value) -> RuntimeResult:
        result = RuntimeResult()
        new_dictionary = self.copy()
        
        if isinstance(other, Dictionary):
            keys = map(lambda e: e.value, list(other.value.keys()))
            values = map(lambda e: e.value, list(other.value.values()))
            other_dictionary = dict(zip(keys, values))

            for key, value in new_dictionary.value.copy().items():
                if key.value in other_dictionary and other_dictionary[key.value] == value.value:
                    del new_dictionary.value[key]

            return result.success(new_dictionary)
        
        return result.failure(RuntimeError(
            self.start_position, other.end_position.copy(),
            f"An object of type {__class__.__name__} can't be subtracted by an object of type {other.__class__.__name__}",
            self.context
        ))
        
    def multiplied_by(self, other: Value) -> RuntimeResult:
        return RuntimeResult().failure(RuntimeError(
            self.start_position, other.end_position,
            f"An object of type {__class__.__name__} can't be multiplied",
            self.context
        ))
        
    def divided_by(self, other: Value) -> RuntimeResult:
        return RuntimeResult().failure(RuntimeError(
            self.start_position, other.end_position,
            f"An object of type {__class__.__name__} can't be divided",
            self.context
        ))

    def powered_by(self, other: Value) -> RuntimeResult:
        return RuntimeResult().failure(RuntimeError(
            self.start_position, other.end_position,
            f"An object of type {__class__.__name__} can't be raised to a power",
            self.context
        ))
    
    ## Comparaisons

    def is_equals_to(self, other) -> RuntimeResult:
        result = RuntimeResult()

        if isinstance(other, Dictionary):
            self_keys = map(lambda e: e.value, list(self.value.keys()))
            self_values =  map(lambda e: e.value, list(self.value.values()))
            self_dictionary = dict(zip(self_keys, self_values))

            other_keys = map(lambda e: e.value, list(other.value.keys()))
            other_values =  map(lambda e: e.value, list(other.value.values()))
            other_dictionary = dict(zip(other_keys, other_values))

            return result.success(Number(self_dictionary == other_dictionary)
                .set_context(self.context)
                .set_position(self.start_position, other.end_position))

        return result.success(Number(0)
            .set_context(self.context)
            .set_position(self.start_position, other.end_position))
    
    def is_not_equals_to(self, other) -> RuntimeResult:
        return super().is_not_equals_to(other)

    def is_greater_than(self, other) -> RuntimeResult:
        result = RuntimeResult()

        if isinstance(other, Dictionary):
            return result.success(Number(len(self.value) > len(other.value))\
                .set_context(self.context)\
                .set_position(self.start_position, other.end_position))

        return result.failure(RuntimeError(
            self.start_position, other.end_position,
            f"An object of type {__class__.__name__} can't be compared with an object of type {type(other).__name__} with a '>' or '>=' operator",
            self.context
        ))

    def is_less_than(self, other) -> RuntimeResult:
        result = RuntimeResult()

        if isinstance(other, Dictionary):
            return result.success(Number(len(self.value) < len(other.value))\
                .set_context(self.context)\
                .set_position(self.start_position, other.end_position))

        return result.failure(RuntimeError(
            self.start_position, other.end_position,
            f"An object of type {__class__.__name__} can't be compared with an object of type {type(other).__name__} with a '>' or '>=' operator",
            self.context
        ))

    def is_greater_or_equals(self, other) -> RuntimeResult:
        return super().is_greater_or_equals(other)

    def is_less_or_equals(self, other) -> RuntimeResult:
        return super().is_less_or_equals(other)
    
    ## Logical operators

    def and_(self, other) -> RuntimeResult:
        return super().and_(other)
    
    def or_(self, other) -> RuntimeResult:
        return super().or_(other)
    
    def not_(self) -> RuntimeResult:
        return super().not_()
    
    ## Conversion

    def to_boolean(self) -> RuntimeResult:
        return RuntimeResult().success(Number(len(self.value) > 0))
    
    def to_number(self) -> RuntimeResult:
        return RuntimeResult().success(Number(len(self.value)))

    def to_text(self) -> RuntimeResult:
        return RuntimeResult().success(Text(repr(self)))

    def to_list(self) -> RuntimeResult:
        return RuntimeResult().failure(RuntimeError(
            self.start_position, self.end_position,
            f"An object of type {__class__.__name__} can't be casted to a list",
            self.context
        ))

    def to_built_in(self) -> RuntimeResult:
        return RuntimeResult().failure(RuntimeError(
            self.start_position, self.end_position,
            f"An object of type {__class__.__name__} can't be casted to a built-in",
            self.context
        ))


class Null(Value):
    def __init__(self, value = None):
        super().__init__(None)

    def set_position(self, start_position = None, end_position = None):
        return super().set_position(start_position, end_position)
    
    def set_context(self, context = None):
        return super().set_context(context)
    
    def copy(self):
        copy = Null()
        copy.set_position(self.start_position, self.end_position)
        copy.set_context(self.context)

        return copy
    
    def __str__(self) -> str:
        return 'null'
    
    def __repr__(self) -> str:
        return str(self)
    
    ## Execute

    def execute(self, arguments: list[Value]) -> RuntimeResult:
        return RuntimeResult().failure(RuntimeError(
            self.start_position, self.end_position,
            f"An object of type {__class__.__name__} can't be executed",
            self.context
        ))

    ## Index

    def index(self, other: Value) -> RuntimeResult:
        return RuntimeResult().failure(RuntimeError(
            self.start_position, other.end_position.copy().advance(),
            f"An object of type {__class__.__name__} can't be indexed",
            self.context
        ))
    
    def assign_index(self, index: Value, value: Value) -> RuntimeResult:
        return RuntimeResult().failure(RuntimeError(
            self.start_position, index.end_position.copy().advance(),
            f"An object of type {__class__.__name__} does not support index assignment",
            self.context
        ))
    
    ## Binary Operations

    def added_to(self, other: Value) -> RuntimeResult:
        if isinstance(other, Text):
            return RuntimeResult().success(Text(str(self) + other.value))

        return RuntimeResult().failure(RuntimeError(
            self.start_position, other.end_position,
            f"An object of type {__class__.__name__} can't be added to an object of type {other.__class__.__name__}",
            self.context
        ))
        
    def subtracted_by(self, other: Value) -> RuntimeResult:
        return RuntimeResult().failure(RuntimeError(
            self.start_position, other.end_position,
            f"An object of type {__class__.__name__} can't be subtracted to",
            self.context
        ))
        
    def multiplied_by(self, other: Value) -> RuntimeResult:
        return RuntimeResult().failure(RuntimeError(
            self.start_position, other.end_position,
            f"An object of type {__class__.__name__} can't be multiplied",
            self.context
        ))
        
    def divided_by(self, other: Value) -> RuntimeResult:
        return RuntimeResult().failure(RuntimeError(
            self.start_position, other.end_position,
            f"An object of type {__class__.__name__} can't be divided",
            self.context
        ))

    def powered_by(self, other: Value) -> RuntimeResult:
        return RuntimeResult().failure(RuntimeError(
            self.start_position, other.end_position,
            f"An object of type {__class__.__name__} can't be raised to a power",
            self.context
        ))
    
    ## Comparaisons

    def is_equals_to(self, other) -> RuntimeResult:
        result = RuntimeResult()

        if isinstance(other, Null):
            return result.success(Number(1)
                .set_context(self.context)
                .set_position(self.start_position, other.end_position))

        return result.success(Number(0)
            .set_context(self.context)
            .set_position(self.start_position, other.end_position))
    
    def is_not_equals_to(self, other) -> RuntimeResult:
        return super().is_not_equals_to(other)

    def is_greater_than(self, other) -> RuntimeResult:
        return RuntimeResult().failure(RuntimeError(
            self.start_position, other.end_position,
            f"An object of type {__class__.__name__} can't be compared with a '>' or '>=' operator",
            self.context
        ))

    def is_less_than(self, other) -> RuntimeResult:
        return (None, RuntimeError(
            self.start_position, other.end_position,
            f"An object of type {__class__.__name__} can't be compared with a '<' or '<=' operator",
            self.context
        ))

    def is_greater_or_equals(self, other) -> RuntimeResult:
        return super().is_greater_or_equals(other)

    def is_less_or_equals(self, other) -> RuntimeResult:
        return super().is_less_or_equals(other)
    
    ## Logical operators

    def and_(self, other) -> RuntimeResult:
        return super().and_(other)
    
    def or_(self, other) -> RuntimeResult:
        return super().or_(other)
    
    def not_(self) -> RuntimeResult:
        return super().not_()
    
    ## Conversion

    def to_boolean(self) -> RuntimeResult:
        return RuntimeResult().success(Number(0))
    
    def to_number(self) -> RuntimeResult:
        return RuntimeResult().success(Number(0))

    def to_text(self) -> RuntimeResult:
        return RuntimeResult().success(Text(str(self)))

    def to_list(self) -> RuntimeResult:
        return RuntimeResult().success(List([self]))

    def to_built_in(self) -> RuntimeResult:
        return RuntimeResult().failure(RuntimeError(
            self.start_position, self.end_position,
            f"An object of type {__class__.__name__} can't be casted to a built-in",
            self.context
        ))


class BuiltIn(Value):
    def __init__(self, value):
        super().__init__(value)

        self.base_value = None

        try: self.name = [key for key, value in built_ins.items() if value == self.value][0]
        except: self.name = None

    def set_position(self, start_position = None, end_position = None):
        return super().set_position(start_position, end_position)
    
    def set_context(self, context = None):
        return super().set_context(context)
    
    def copy(self):
        copy = BuiltIn(self.value)
        copy.base_value = self.base_value
        copy.set_position(self.start_position, self.end_position)
        copy.set_context(self.context)

        return copy
    
    def __str__(self) -> str:
        return f'BuiltIn{f": {self.name}" if self.name is not None else ""}'

    def __repr__(self) -> str:
        return str(self)
    
    ## Execute

    def execute(self, arguments: list[Value]) -> RuntimeResult:
        result = RuntimeResult()

        if self.base_value is None:
            value = result.register(self.value(self.context, self.start_position, self.end_position, *arguments))
        else:
            value = result.register(self.value(self.context, self.start_position, self.end_position, self.base_value, *arguments))

        if result.error: return result

        return result.success(value.set_context(self.context).set_position(self.start_position, self.end_position))

    ## Index

    def index(self, other: Value) -> RuntimeResult:
        return RuntimeResult().failure(RuntimeError(
            self.start_position, other.end_position.copy().advance(),
            f"An object of type {__class__.__name__} can't be indexed",
            self.context
        ))
    
    def assign_index(self, index: Value, value: Value) -> RuntimeResult:
        return RuntimeResult().failure(RuntimeError(
            self.start_position, index.end_position.copy().advance(),
            f"An object of type {__class__.__name__} does not support index assignment",
            self.context
        ))

    ## Binary Operations

    def added_to(self, other: Value) -> RuntimeResult:
        return RuntimeResult().failure(RuntimeError(
            self.start_position, other.end_position,
            f"An object of type {__class__.__name__} can't be added",
            self.context
        ))
        
    def subtracted_by(self, other: Value) -> RuntimeResult:
        return RuntimeResult().failure(RuntimeError(
            self.start_position, other.end_position,
            f"An object of type {__class__.__name__} can't be subtracted to",
            self.context
        ))
        
    def multiplied_by(self, other: Value) -> RuntimeResult:
        return RuntimeResult().failure(RuntimeError(
            self.start_position, other.end_position,
            f"An object of type {__class__.__name__} can't be multiplied",
            self.context
        ))
        
    def divided_by(self, other: Value) -> RuntimeResult:
        return RuntimeResult().failure(RuntimeError(
            self.start_position, other.end_position,
            f"An object of type {__class__.__name__} can't be divided",
            self.context
        ))

    def powered_by(self, other: Value) -> RuntimeResult:
        return (None, RuntimeError(
            self.start_position, other.end_position,
            f"An object of type {__class__.__name__} can't be raised to a power",
            self.context
        ))
    
    ## Comparaisons

    def is_equals_to(self, other) -> RuntimeResult:
        result = RuntimeResult()

        if isinstance(other, BuiltIn):
            return result.success(Number(self.value == other.value)
                .set_context(self.context)
                .set_position(self.start_position, other.end_position))

        return result.success(Number(0)
            .set_context(self.context)
            .set_position(self.start_position, other.end_position))
    
    def is_not_equals_to(self, other) -> RuntimeResult:
        return super().is_not_equals_to(other)

    def is_greater_than(self, other) -> RuntimeResult:
        return RuntimeResult().failure(RuntimeError(
            self.start_position, other.end_position,
            f"An object of type {__class__.__name__} can't be compared with a '>' or '>=' operator",
            self.context
        ))

    def is_less_than(self, other) -> RuntimeResult:
        return RuntimeResult().failure(RuntimeError(
            self.start_position, other.end_position,
            f"An object of type {__class__.__name__} can't be compared with a '<' or '<=' operator",
            self.context
        ))

    def is_greater_or_equals(self, other) -> RuntimeResult:
        return super().is_greater_or_equals(other)

    def is_less_or_equals(self, other) -> RuntimeResult:
        return super().is_less_or_equals(other)
    
    ## Logical operators

    def and_(self, other) -> RuntimeResult:
        return super().and_(other)
    
    def or_(self, other) -> RuntimeResult:
        return super().or_(other)
    
    def not_(self) -> RuntimeResult:
        return super().not_()
    
    ## Conversion

    def to_boolean(self) -> RuntimeResult:
        return RuntimeResult().failure(RuntimeError(
            self.start_position, self.end_position,
            f"An object of type {__class__.__name__} can't be casted to a boolean",
            self.context
        ))
    
    def to_number(self) -> RuntimeResult:
        return RuntimeResult().failure(RuntimeError(
            self.start_position, self.end_position,
            f"An object of type {__class__.__name__} can't be casted to a number",
            self.context
        ))

    def to_text(self) -> RuntimeResult:
        return RuntimeResult().success(Text(self.name))

    def to_list(self) -> RuntimeResult:
        return RuntimeResult().success(List([self]))

    def to_built_in(self) -> RuntimeResult:
        return RuntimeResult().success(self)

#endregion

#region CONTEXT

class Context:
    def __init__(self, display_name, parent = None, parent_entry_position = None):
        self.display_name = display_name
        self.parent = parent
        self.parent_entry_position = parent_entry_position
        self.symbol_table = None

#endregion

#region SYMBOL TABLE

class SymbolTable:
    def __init__(self, parent = None):
        self.symbols = {}
        self.parent = parent

    def copy(self):
        copy = SymbolTable()
        copy.symbols = self.symbols.copy()
        copy.parent = self.parent
        
        return copy

    def get(self, key: Value, explicit: bool = False):
        value = self.symbols.get(key.value, None)

        if (not explicit) and (value is None) and isinstance(self.parent, SymbolTable):
            return self.parent.get(key, explicit)
        
        return value
    
    def set(self, key: Value, value: Value):
        self.symbols[key.value] = value

    def remove(self, key: Value):
        del self.symbols[key.value]

#endregion

#region DEFAULT CONTEXT

default_context = Context('Program')
default_symbol_table = SymbolTable()
default_context.symbol_table = default_symbol_table

global_context = Context('Program')
global_symbol_table = SymbolTable()

## Default variables

default_symbol_table.set(Text('true'), Number(1))
default_symbol_table.set(Text('false'), Number(0))
default_symbol_table.set(Text('null'), Null())

# AI

syntax = r"""
## Core Types

| Type                  | Syntax                           | Description                                                                                     |
| --------------------- | -------------------------------- | ----------------------------------------------------------------------------------------------- |
| **Text**              | `"Single line"`, `{ Multiline }` | All text is executable via `()`. Multiline text using `{}` can be nested.                       |
| **Number**            | `3.14`, `42`                     | One numeric type for all.                                                                       |
| **List**              | `[1, 2, 3]`                      | A flexible, ordered container.                                                                  |
| **Dictionary**        | `\|"a": 1, "b": 2\|`             | An object containing key-value mappings.                                                        |
| **Null**              | `Null()`                         | A single unit of nothingness.                                                                   |
| **Built-in function** | `BuiltIn("print")`               | Built-ins are functions that perform low-level operations, meaning you can't access their code. |

## Variables

### Variable syntax

- `$var`: Gets the value or assigns to `"var"`. Non-conflicting variable names can skip the `$` symbol.
- `$(...)`: Gets the value or assigns to a variable from a dynamic name

### Reading and assignment

- `$var`: Reads the value of a variable
- `$var = "value"`: Assigns a value to a variable

### Example

```runtime
$var = "Hello World!"
$print($var) // > Hello World!

// Non-conflicting names can skip the $ symbol
print(var) // > Hello World!
```

## Comments

- **Single line:** `// Comment`
- **Multiline:** `/* Comment */`

## Functions

- Functions are declared by defining text variables. Any text is executable via `()`.
- You can get the arguments passed to the function from the `arguments` default variable.
- The last expression on a function will be returned by default.

### Example

```runtime
get_input = {
    input("INPUT: " + arguments[0])
}

name = get_input("Enter your name") // > INPUT: Enter your name
print("Your name is " + name) // > Your name is <name>
```
## Methods

- Methods are functions that can be executed using the `object.method()` syntax.
- Methods are functions that follow `Type~method` naming convention.
- All functions following the naming convetion can be used as methods.
- When a method is called, the first argument passed to the function is the object it's being called on.

### Example

```runtime
// List~append is a default method
list = [1, 2, 3]
list = list.append(4)
print(list) // > [1, 2, 3, 4]

// Overwrite the append method to remove elements instead
List~append = {
    list = arguments[0]
    element = arguments[1]
    list.remove(element)
}

print(list.append(4)) // > [1, 2, 3]

// Declare a custom method
Text~shout = {
    text = arguments[0]
    text.to_uppercase() + "!!!"
}

print("runtime".shout()) // > RUNTIME!!!
```

## Lists

- Lists are defined with comma-separated values encapsulated between brackets. 
- To read an element, use `$list[i]`.
- To overwrite an element, use `$list[i] = "value"`.

### Example

```runtime
list = [1, 2, 3]
list[0] = 42
print(list[0]) // > 42
```

## Dictionaries

- Dictionaries are defined with comma-separated key-value pairs encapsulated between pipes.
- To read a value from its key, use `$dictionary["key"]`.
- To assign a value to a key, use `$dictionary["key"] = "value"`.
- `$dictionary.key` reads a key, as long as it isn't shadowed by a method.
- `$dictionary.key = "value"` assigns to a key.

### Example

```runtime
dictionary = |
    "a": 1,
    "b": 2,
    "c": 3
|

dictionary["a"] = 42
print(dictionary["a"]) // > 42
```

## Scopes

When a text object is executed, a new scope is created for its variables. Variables in parent scopes are visible by default, as long as they aren't shadowed by variables with the same name in children scopes.

- To access a variable in the current scope that has been shadowed by parent scopes, use `[0]$var`
- To access a variable in the parent scope that has been shadowed in the current one, use `[1]$var`
- To access a shadowed variable two levels up in the hierarchy, use `[2]$var`, and so on
- To access a variable in the global scope, use `[global]$var`
- To access a default variable that has been overwritten, use `[default]$var`

### Default scope

#### Default variables

| Variable | Type     | Default value | 
| -------- | -------- | ------------- |
| `true`   | `Number` | `1`           |
| `false`  | `Number` | `0`           |
| `null `  | `Null`   | `null`        |

#### Default built-ins

| Function     | Parameters          | Description                                                                       | Return type |
| ------------ | ------------------- | --------------------------------------------------------------------------------- | ----------- |
| `print`      | `*objects: object`  | Prints one or more objects to the console.                                        | `Null`      |
| `input`      | `message?: object`  | Returns the user input from the console and displays an optional message.         | `Text`      |
| `length`     | `object: object`    | Returns the length of the provided object.                                        | `Number`    |
| `wait`       | `seconds: Number`   | Interrupts the thread for the provided amount of seconds.                         | `Null`      |
| `type`       | `object: object`    | Returns the name of the type of the provided object.                              | `Text`      |
| `is_defined` | `name: object`      | Returns `1` if a variable with the provided name is defined, and `0` if it isn't. | `Number`    |

#### Default constructors

| Constructor                            | Description                                                    |
| -------------------------------------- | -------------------------------------------------------------- |
| `Text(object: object)`                 | Constructs a new text object from the provided value.          |
| `Number(object: object)`               | Constructs a new number object from the provided value.        |
| `List(*objects: object)              ` | Constructs a new list from the provided elements.              |
| `Dictionary(keys: List, values: List)` | Constructs a new dictionary from the provided keys and values. |
| `Null()`                               | Constructs a new null object.                                  |
| `BuiltIn(name: Text)`                  | Returns the default value of a default built-in from its name  |

#### Default dictionaries

- `ai`
    | Key          | Value type | Parameters     | Description                                         | Return type |
    | ------------ | ---------- | -------------- | --------------------------------------------------- | ----------- |
    | `"prompt"`   | `BuiltIn`  | `prompt: Text` | Returns the response of an AI to your prompt.       | `Text`      |
    | `"vibecode"` | `BuiltIn`  | `prompt: Text` | Returns valid RUNTIME code fulfilling your prompt.  | `Text`      |

- `math`
    | Key                | Value type | Parameters                             | Description                                           | Return type |
    | ------------------ | ---------- | -------------------------------------- | ----------------------------------------------------- | ----------- |
    | `"pi"`             | `Number`   | —                                      | Constant π: 3.1415926535...                           | —           |
    | `"e"`              | `Number`   | —                                      | Constant e: 2.7182818284...                           | —           |
    | `"ceiling"`        | `BuiltIn`  | `number: Number`                       | Rounds the number up to the nearest integer.          | `Number`    |
    | `"floor"`          | `BuiltIn`  | `number: Number`                       | Rounds the number down to the nearest integer.        | `Number`    |
    | `"round"`          | `BuiltIn`  | `number: Number`                       | Rounds the number to the nearest integer.             | `Number`    |
    | `"absolute_value"` | `BuiltIn`  | `number: Number`                       | Returns the the absolute value of `number`.           | `Number`    |
    | `"square"`         | `BuiltIn`  | `number: Number`                       | Returns `number` squared.                             | `Number`    |
    | `"cube"`           | `BuiltIn`  | `number: Number`                       | Returns `number` cubed.                               | `Number`    |
    | `"power"`          | `BuiltIn`  | `base: Number, exponent: Number`       | Raises the ``base`` to the power of the ``exponent``. | `Number`    |
    | `"square_root"`    | `BuiltIn`  | `number: Number`                       | Returns the square root of `number`.                  | `Number`    |
    | `"cubic_root"`     | `BuiltIn`  | `number: Number`                       | Returns the cubic root of `number`.                   | `Number`    |
    | `"root"`           | `BuiltIn`  | `value: Number, degree: Number`        | Returns the `degree`-th root of `value`.              | `Number`    |
    | `"logarithm"`      | `BuiltIn`  | `value: Number, base: Number = math.e` | Returns the logarithm of `value` from a given `base`. | `Number`    |
    | `"factorial"`      | `BuiltIn`  | `number: Number`                       | Returns the factorial of `number`.                    | `Number`    |
    | `"random"`         | `BuiltIn`  | `min: Number = 0, max: Number = 1`     | Returns a random number in the provided range.        | `Number`    |

#### Default methods

##### Lists

| Function            | Parameters                       | Description                                                                                                     | Return type |
| ------------------- | -------------------------------- | --------------------------------------------------------------------------------------------------------------- | ----------- |
| `List.append`       | `element: object`                | Adds the `element` to the end of the list.                                                                      | `List`      |
| `List.extend`       | `other: List`                    | Adds all elements in `other` to the end of the list.                                                            | `List`      |
| `List.remove`       | `element: object`                | Removes the first occurence of `element` from the list.                                                         | `List`      |
| `List.remove_all`   | `element: object`                | Removes all occurrences of `elements` from the list.                                                            | `List`      |
| `List.subtract`     | `other: List`                    | Removes the first occurence of each element in `other` from the list.                                           | `List`      |
| `List.subtract_all` | `other: List`                    | Removes all occurences of each element in `other` from the list.                                                | `List`      |
| `List.contains`     | `element: object`                | Returns `1` if the list contains the `element`, and `0` if it doesn't.                                          | `Number`    |
| `List.index_of`     | `element: object`                | Returns the index of the first ocurrence of `element` in the list.                                              | `Number`    |
| `List.insert`       | `index: Number, element: object` | Adds the `element` at the provided `index`.                                                                     | `List`      |
| `List.pop`          | `index: Number`                  | Removes the element found at the provided `index`.                                                              | `List`      |
| `List.count`        | `element: object`                | Returns the number of occurences of `element` in the list.                                                      | `Number`    |
| `List.slice`        | `start: Number, end: Number`     | Returns a sublist from `start` (inclusive) to `end` (exclusive).                                                | `List`      |
| `List.map`          | `function: Text`                 | Executes the given function for each element (with `arguments[0] = element`) and returns the results as a list. | `List`      |

##### Dictionaries

| Function                 | Parameters                   | Description                                                                       | Return type  |
| ------------------------ | ---------------------------- | --------------------------------------------------------------------------------- | ------------ |
| `Dictionary.merge`       | `other: Dictionary`          | Merges the dictionaries. Identical keys will be overwritten by values in `other`. | `Dictionary` |
| `Dictionary.difference`  | `other: Dictionary`          | Removes identical key-value pairs from the dictionary.                            | `Dictionary` |
| `Dictionary.add`         | `key: object, value: object` | Adds a pair from the provided `key` and `value`                                   | `Dictionary` |
| `Dictionary.remove`      | `key: object`                | Removes a key-value pair from its `key`.                                          | `Dictionary` |
| `Dictionary.remove_many` | `keys: List`                 | Removes key-value pairs from their `keys`.                                        | `Dictionary` |
| `Dictionary.keys`        |                              | Returns a list of all keys in the dictionary.                                     | `List`       |
| `Dictionary.values`      |                              | Returns a list of all values in the dictionary.                                   | `List`       |

##### Text

| Function             | Parameters     | Description                                             | Return type |
| -------------------- | -------------- | ------------------------------------------------------- | ----------- |
| `Text.strip`         |                | Removes leading and trailing whitespaces from the text. | `Text`      |
| `Text.to_lowercase`  |                | Returns the lowercase equivalent of the text object.    | `Text`      |
| `Text.to_uppercase`  |                | Returns the upper equivalent of the text object.        | `Text`      |
| `Text.add_prefix`    | `prefix: Text` | Adds a `prefix` to the text object.                     | `Text`      |
| `Text.remove_prefix` | `prefix: Text` | Removes a `prefix` from the text object, if present.    | `Text`      |
| `Text.add_suffix`    | `suffix: Text` | Adds a `suffix` to the text object.                     | `Text`      |
| `Text.remove_suffix` | `suffix: Text` | Removes a `suffix` from the text object, if present.    | `Text`      |

## Flow control

### Conditions

-   `true` and `false` are variables with the default values of 1 and 0 respectivelly
-   **Boolean operators:** `and`, `or`, `not`
-   **Comparison operators:** `>`, `<`, `>=`, `<=`, `==`, `!=`

### Branching

-   **If**: Executes the provided object if the provided condition is met

    ```runtime
    if (true) {
        print("Hello World!")
    }
    ```

-   **Else**: Executes the provided object or if statement in case the condition of the previous if statement wasn't met

    ```runtime
    number = Number(input())

    if (number == 1) {
        print("Number is 1")
    } else if (number == 2) {
        print("Number is 2")
    } else {
        print("Number is 3 or more")
    }
    ```

### Loops

-   **While**: If the provided condition is met, the provided object is executed and the code block repeats.

    ```runtime
    i = 0

    while (i < 3) {
        i = i + 1
        print("Loop " + i)
    }

    print("Loop ended")

    // > Loop 1
    // > Loop 2
    // > Loop 3
    // > Loop ended
    ```

"""

APP_NAME = "runtime"
CONFIG_DIR = Path(user_config_dir(APP_NAME))
CONFIG_FILE = CONFIG_DIR / "config.json"

def load_config():
    if not CONFIG_FILE.exists():
        return {}
    try:
        return json.loads(CONFIG_FILE.read_text())
    except json.JSONDecodeError:
        return {}

def ai_prompt(context, start_position, end_position, *arguments):
    if len(arguments) < 1:
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Missing argument: prompt',
            context
        ))

    try:
        user_prompt = arguments[0].value
        config = load_config()

        if "api_key" in config:
            api_key = config["api_key"]
        else:
            return RuntimeResult().failure(RuntimeError(
                start_position, end_position,
                'Hack Club AI API key was not provided. Run `runtime --set-api-key [YOUR_API_KEY]`.',
                context
            ))

        url = 'https://ai.hackclub.com/proxy/v1/chat/completions'

        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + api_key
        }

        data = {
            "model": "google/gemini-3-flash-preview",
            "messages": [
                {
                    "role": "user",
                    "content": user_prompt
                }    
            ]
        }

        result = requests.post(url, data = json.dumps(data), headers = headers)
        result = json.loads(result.text, strict = False)

        text = result["choices"][0]["message"]["content"]

        try:
            index = text.index("</think>") + len("</think>")
            text = text[index:].removeprefix("\n\n")
        except:
            pass

        return RuntimeResult().success(Text(text).set_context(context))
    
    except Exception as e:
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'AI request failed: ' + str(e),
            context
        ))

def ai_vibecode(context, start_position, end_position, *arguments):
    if len(arguments) < 1:
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Missing argument: prompt',
            context
        ))

    user_prompt = arguments[0].value
    
    system_prompt = r"""
# SYSTEM INSTRUCTIONS

You are an expert in creating computer code in the RUNTIME programming language. Understand the user's input and think step by step about how to best accomplish this goal using the following instructions.

# RUNTIME SYNTAX
""" + syntax + r"""
# OUTPUT INSTRUCTIONS

- Output ONLY valid RUNTIME code.
- Do NOT output ANYTHING ELSE, just the requested code.

# INPUT

""" + user_prompt

    result = RuntimeResult()

    output = result.register(ai_prompt(context, start_position, end_position, Text(system_prompt)))
    if result.error: return output

    output.value = output.value.strip().removeprefix('```runtime').strip().removesuffix('```')
    return result.success(output)

default_symbol_table.set(Text('ai'), Dictionary({ 
    Text("prompt"): BuiltIn(ai_prompt).set_context(global_context),
    Text("vibecode"): BuiltIn(ai_vibecode).set_context(global_context)
}))

# Math

def math_ceiling(context, start_position, end_position, *arguments):
    if len(arguments) < 1:
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Missing argument: number',
            context
        ))
    
    if not isinstance(arguments[0], Number):
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Type error: first argument must be a number',
            context
        ))

    value = arguments[0].value
    return RuntimeResult().success(Number(math.ceil(value)).set_context(context))

def math_floor(context, start_position, end_position, *arguments):
    if len(arguments) < 1:
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Missing argument: number',
            context
        ))
    
    if not isinstance(arguments[0], Number):
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Type error: first argument must be a number',
            context
        ))

    value = arguments[0].value
    return RuntimeResult().success(Number(math.floor(value)).set_context(context))

def math_round(context, start_position, end_position, *arguments):
    if len(arguments) < 1:
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Missing argument: number',
            context
        ))
    
    if not isinstance(arguments[0], Number):
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Type error: first argument must be a number',
            context
        ))

    value = arguments[0].value
    return RuntimeResult().success(Number(round(value)).set_context(context))

def math_absolute_value(context, start_position, end_position, *arguments):
    value = arguments[0].value
    return RuntimeResult().success(Number(abs(value)).set_context(context))

def math_square(context, start_position, end_position, *arguments):
    if len(arguments) < 1:
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Missing argument: number',
            context
        ))
    
    if not isinstance(arguments[0], Number):
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Type error: first argument must be a number',
            context
        ))

    value = arguments[0].value
    return RuntimeResult().success(Number(math.pow(value, 2)).set_context(context))

def math_cube(context, start_position, end_position, *arguments):
    if len(arguments) < 1:
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Missing argument: number',
            context
        ))
    
    if not isinstance(arguments[0], Number):
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Type error: first argument must be a number',
            context
        ))

    value = arguments[0].value
    return RuntimeResult().success(Number(math.pow(value, 3)).set_context(context))

def math_power(context, start_position, end_position, *arguments):
    if len(arguments) < 1:
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Missing argument: base',
            context
        ))
    
    if len(arguments) < 2:
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Missing argument: exponent',
            context
        ))
    
    if not isinstance(arguments[0], Number):
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Type error: first argument must be a number',
            context
        ))
    
    if not isinstance(arguments[1], Number):
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Type error: second argument must be a number',
            context
        ))

    value1 = arguments[0].value
    value2 = arguments[1].value
    return RuntimeResult().success(Number(math.pow(value1, value2)).set_context(context))

def math_square_root(context, start_position, end_position, *arguments):
    if len(arguments) < 1:
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Missing argument: number',
            context
        ))
    
    if not isinstance(arguments[0], Number):
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Type error: first argument must be a number',
            context
        ))

    value = arguments[0].value
    return RuntimeResult().success(Number(math.sqrt(value)).set_context(context))

def math_cubic_root(context, start_position, end_position, *arguments):
    if len(arguments) < 1:
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Missing argument: number',
            context
        ))
    
    if not isinstance(arguments[0], Number):
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Type error: first argument must be a number',
            context
        ))

    value = arguments[0].value
    return RuntimeResult().success(Number(math.cbrt(value)).set_context(context))

def math_root(context, start_position, end_position, *arguments):
    if len(arguments) < 1:
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Missing argument: value',
            context
        ))
    
    if len(arguments) < 2:
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Missing argument: degree',
            context
        ))
    
    if not isinstance(arguments[0], Number):
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Type error: first argument must be a number',
            context
        ))
    
    if not isinstance(arguments[1], Number):
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Type error: second argument must be a number',
            context
        ))

    value1 = arguments[0].value
    value2 = arguments[1].value
    return RuntimeResult().success(Number(math.pow(value1, 1 / value2)).set_context(context))

def math_logarithm(context, start_position, end_position, *arguments):
    if len(arguments) < 1:
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Missing argument: value',
            context
        ))
    
    if not isinstance(arguments[0], Number):
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Type error: first argument must be a number',
            context
        ))
    
    if len(arguments) >= 2 and not isinstance(arguments[1], Number):
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Type error: second argument must be a number',
            context
        ))

    value1 = arguments[0].value

    if len(arguments) > 1:
        value2 = arguments[1].value
    else:
        value2 = math.e

    return RuntimeResult().success(Number(math.log(value1, value2)).set_context(context))

def math_factorial(context, start_position, end_position, *arguments):
    if len(arguments) < 1:
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Missing argument: value',
            context
        ))
    
    if not isinstance(arguments[0], Number):
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Type error: first argument must be a number',
            context
        ))

    if not arguments[0].value.is_integer():
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'First argument must be a whole number',
            context
        ))

    value = int(arguments[0].value)

    try:
        factorial = math.factorial(value)
        float_factorial = float(factorial)
        return RuntimeResult().success(Number(float_factorial).set_context(context))
    except:
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Result exceeds the number digit limit',
            context
        ))

def math_random(context, start_position, end_position, *arguments):    
    if len(arguments) > 0 and not isinstance(arguments[0], Number):
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Type error: first argument must be a number',
            context
        ))
    
    if len(arguments) > 1 and not isinstance(arguments[1], Number):
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Type error: second argument must be a number',
            context
        ))

    if len(arguments) == 0:
        min = 0
        max = 1
    elif len(arguments) == 1:
        min = 0
        max = arguments[0].value
    else:
        min = arguments[0].value
        max = arguments[1].value

    return RuntimeResult().success(Number(random.uniform(min, max)).set_context(context))

default_symbol_table.set(Text('math'), Dictionary({ 
    Text("e"): Number(math.e).set_context(global_context),
    Text("pi"): Number(math.pi).set_context(global_context),
    Text("ceiling"): BuiltIn(math_ceiling).set_context(global_context),
    Text("floor"): BuiltIn(math_floor).set_context(global_context),
    Text("round"): BuiltIn(math_round).set_context(global_context),
    Text("absolute_value"): BuiltIn(math_absolute_value).set_context(global_context),
    Text("square"): BuiltIn(math_square).set_context(global_context),
    Text("cube"): BuiltIn(math_cube).set_context(global_context),
    Text("power"): BuiltIn(math_power).set_context(global_context),
    Text("square_root"): BuiltIn(math_square_root).set_context(global_context),
    Text("cubic_root"): BuiltIn(math_cubic_root).set_context(global_context),
    Text("root"): BuiltIn(math_root).set_context(global_context),
    Text("logarithm"): BuiltIn(math_logarithm).set_context(global_context),
    Text("factorial"): BuiltIn(math_factorial).set_context(global_context),
    Text("random"): BuiltIn(math_random).set_context(global_context)
}))

## Built-ins

def print_value(context, start_position, end_position, *arguments):
    print(*arguments)
    return RuntimeResult().success(Null().set_context(context))

def input_value(context, start_position, end_position, *arguments):
    if len(arguments) > 0:
        string = input(arguments[0].to_text().value)
    else:
        string = input()

    return RuntimeResult().success(Text(string).set_context(context))

def length_of_value(context,start_position, end_position,  *arguments):
    if len(arguments) < 1:
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Missing argument: object',
            context
        ))

    return RuntimeResult().success(Number(len(get_object_from_value(arguments[0]))).set_context(context))

def sleep_value(context, start_position, end_position, *arguments):
    if len(arguments) < 1:
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Missing argument: object',
            context
        ))

    if not isinstance(arguments[0], Number):
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Type error: first argument must be a number',
            context
        ))

    sleep(get_object_from_value(arguments[0]))
    return RuntimeResult().success(Null().set_context(context))

def type_of_value(context, start_position, end_position, *arguments):
    if len(arguments) < 1:
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Missing argument: object',
            context
        ))

    return RuntimeResult().success(Text(type(arguments[0]).__name__).set_context(context))

def convert_value(context, start_position, end_position, function_name, *arguments):
    if len(arguments) < 1:
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Missing argument: object',
            context
        ))

    return getattr(arguments[0], function_name)()

# Methods

def List_append(context, start_position, end_position, *arguments):
    if len(arguments) < 1:
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Method must be called on a list',
            context
        ))
    
    if len(arguments) < 2:
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Missing argument: element',
            context
        ))
    
    if not isinstance(arguments[0], List):
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Type error: method must be called on a list',
            context
        ))

    list_object = arguments[0].copy()
    list_object.value.append(arguments[1])

    return RuntimeResult().success(list_object.set_context(context))

def List_remove(context, start_position, end_position, *arguments):
    if len(arguments) < 1:
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Method must be called on a list',
            context
        ))
    
    if len(arguments) < 2:
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Missing argument: element',
            context
        ))
    
    if not isinstance(arguments[0], List):
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Type error: method must be called on a list',
            context
        ))

    list_object = arguments[0].copy()
    index = 0
    found = False

    for element in list_object.value:
        if element.value == arguments[1].value:
            found = True
            break
        
        index += 1

    if found:
        list_object.value.pop(index)

    return RuntimeResult().success(list_object.set_context(context))

def List_contains(context, start_position, end_position, *arguments):
    if len(arguments) < 1:
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Method must be called on a list',
            context
        ))
    
    if len(arguments) < 2:
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Missing argument: element',
            context
        ))
    
    if not isinstance(arguments[0], List):
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Type error: method must be called on a list',
            context
        ))

    object_list = list(map(lambda e: e.value, arguments[0].value))
    return RuntimeResult().success(Number(arguments[1].value in object_list).set_context(context))

def List_extend(context, start_position, end_position, *arguments):
    if len(arguments) < 1:
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Method must be called on a listt',
            context
        ))
    
    if len(arguments) < 2:
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Missing argument: other',
            context
        ))
    
    if not isinstance(arguments[0], List):
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Type error: method must be called on a list',
            context
        ))
    
    if not isinstance(arguments[1], List):
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Type error: first argument must be a list',
            context
        ))

    first_list = arguments[0].copy()
    second_list = arguments[1].copy()

    for element in second_list.value:
        first_list.value.append(element)

    return RuntimeResult().success(first_list)

def List_index_of(context, start_position, end_position, *arguments):
    if len(arguments) < 1:
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Method must be called on a list',
            context
        ))
    
    if len(arguments) < 2:
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Missing argument: index',
            context
        ))
    
    if not isinstance(arguments[0], List):
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Type error: method must be called on a list',
            context
        ))
    
    if not isinstance(arguments[1], Number):
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Type error: first argument must be a number',
            context
        ))

    list_object = arguments[0].copy()
    index = 0
    found = False

    for element in list_object.value:
        if element.value == arguments[1].value:
            found = True
            break
        
        index += 1

    if found:
        return RuntimeResult().success(Number(index).set_context(context))

def List_insert(context, start_position, end_position, *arguments):
    if len(arguments) < 1:
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Method must be called on a list',
            context
        ))
    
    if len(arguments) < 2:
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Missing argument: index',
            context
        ))
    
    if len(arguments) < 3:
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Missing argument: element',
            context
        ))
    
    if not isinstance(arguments[0], List):
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Type error: method must be called on a list',
            context
        ))
    
    if not isinstance(arguments[1], Number):
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Type error: first argument must be a number',
            context
        ))

    if not arguments[1].value.is_integer():
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'First argument must be a whole number',
            context
        ))

    list_object = arguments[0].copy()
    index = arguments[1].copy()
    element = arguments[2].copy()

    list_object.value.insert(int(index.value), element)
    return RuntimeResult().success(list_object.set_context(context))

def List_pop(context, start_position, end_position, *arguments):
    if len(arguments) < 1:
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Method must be called on a list',
            context
        ))
    
    if len(arguments) < 2:
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Missing argument: index',
            context
        ))
    
    if not isinstance(arguments[0], List):
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Type error: method must be called on a list',
            context
        ))
    
    if not isinstance(arguments[1], Number):
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Type error: first argument must be a number',
            context
        ))

    if not arguments[1].value.is_integer():
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'First argument must be a whole number',
            context
        ))

    list_object = arguments[0].copy()
    index = arguments[1].copy()

    list_object.value.pop(int(index.value))
    return RuntimeResult().success(list_object.set_context(context))

def List_count(context, start_position, end_position, *arguments):
    if len(arguments) < 1:
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Method must be called on a list',
            context
        ))
    
    if len(arguments) < 2:
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Missing argument: element',
            context
        ))
    
    if not isinstance(arguments[0], List):
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Type error: method must be called on a list',
            context
        ))

    list_object = arguments[0].copy()
    list_object.value = list(map(lambda e: e.value, list_object.value))

    return RuntimeResult().success(Number(list_object.value.count(arguments[1].value)).set_context(context))

def List_remove_all(context, start_position, end_position, *arguments):
    if len(arguments) < 1:
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Method must be called on a list',
            context
        ))
    
    if len(arguments) < 2:
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Missing argument: element',
            context
        ))
    
    if not isinstance(arguments[0], List):
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Type error: method must be called on a list',
            context
        ))

    list_object = arguments[0].copy()

    for element in list_object.value.copy():
        if element.value == arguments[1].value:
            list_object.value.remove(element)

    return RuntimeResult().success(list_object.set_context(context))

def List_subtract(context, start_position, end_position, *arguments):
    if len(arguments) < 1:
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Method must be called on a list',
            context
        ))
    
    if len(arguments) < 2:
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Missing argument: other',
            context
        ))
    
    if not isinstance(arguments[0], List):
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Type error: method must be called on a list',
            context
        ))
    
    if not isinstance(arguments[1], List):
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Type error: first argument must be a list',
            context
        ))
    
    list_object = arguments[0].copy()
    other = list(map(lambda e: e.value, arguments[1].value))

    indices = []
    index = 0

    for element in list_object.value:
        if element.value in other:
            other.remove(element.value)
            indices.append(index)

        index += 1

    for i in reversed(range(len(list_object.value))):
        if i in indices:
            list_object.value.pop(i)

    return RuntimeResult().success(list_object.set_context(context))

def List_subtract_all(context, start_position, end_position, *arguments):
    if len(arguments) < 1:
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Method must be called on a list',
            context
        ))
    
    if len(arguments) < 2:
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Missing argument: other',
            context
        ))
    
    if not isinstance(arguments[0], List):
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Type error: method must be called on a list',
            context
        ))
    
    if not isinstance(arguments[1], List):
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Type error: first argument must be a list',
            context
        ))

    list_object = arguments[0].copy()
    other = list(map(lambda e: e.value, arguments[1].value))

    indices = []
    index = 0

    for element in list_object.value:
        if element.value in other:
            indices.append(index)

        index += 1

    for i in reversed(range(len(list_object.value))):
        if i in indices:
            list_object.value.pop(i)

    return RuntimeResult().success(list_object.set_context(context))

def List_slice(context, start_position, end_position, *arguments):
    if len(arguments) < 1:
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Method must be called on a list',
            context
        ))
    
    if len(arguments) < 2:
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Missing argument: start',
            context
        ))
    
    if len(arguments) < 3:
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Missing argument: end',
            context
        ))
    
    if not isinstance(arguments[0], List):
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Type error: method must be called on a list',
            context
        ))
    
    if not isinstance(arguments[1], Number):
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Type error: first argument must be a number',
            context
        ))
    
    if not arguments[1].value.is_integer():
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'First argument must be a whole number',
            context
        ))

    if not isinstance(arguments[2], Number):
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Type error: second argument must be a number',
            context
        ))

    if not arguments[2].value.is_integer():
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Second argument must be a whole number',
            context
        ))

    list_object = arguments[0].copy()
    start = int(arguments[1].value)
    end = int(arguments[2].value)

    list_object.value = list_object.value[start:end]
    return RuntimeResult().success(list_object.set_context(context))

def List_map(context, start_position, end_position, *arguments):
    if len(arguments) < 1:
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Method must be called on a list',
            context
        ))
    
    if len(arguments) < 2:
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Missing argument: function',
            context
        ))
    
    if not isinstance(arguments[0], List):
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Type error: method must be called on a list',
            context
        ))
    
    if not isinstance(arguments[1], Text):
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Type error: first argument must be a text object',
            context
        ))

    result = RuntimeResult()
    old_list = arguments[0].copy()
    new_list = List([])
    function = arguments[1]

    for element in old_list.value:
        output = result.register(function.execute([element]))
        new_list.value.append(output)

    return result.success(new_list.set_context(context))


def Dictionary_merge(context, start_position, end_position, *arguments):
    if len(arguments) < 1:
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Method must be called on a dictionary',
            context
        ))
    
    if len(arguments) < 2:
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Missing argument: other',
            context
        ))
    
    if not isinstance(arguments[0], Dictionary):
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Type error: method must be called on a dictionary',
            context
        ))
    
    if not isinstance(arguments[1], Dictionary):
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Type error: first argument must be a dictionary',
            context
        ))

    dictionary = arguments[0].copy()
    dictionary_keys = list(map(lambda e: e.value, dictionary.value.keys()))

    other = arguments[1].copy()
    other.value = { k.value: v.value for (k, v) in zip(other.value.keys(), other.value.values()) }

    for key, value in dictionary.value.items():
        if key.value in list(other.value.keys()):
            dictionary.value[key] = get_value_from_object(other.value[key.value])

    for key, value in other.value.items():
        if key not in dictionary_keys:
            dictionary.value[get_value_from_object(key)] = get_value_from_object(value)

    return RuntimeResult().success(dictionary.set_context(context))

def Dictionary_difference(context, start_position, end_position, *arguments):
    if len(arguments) < 1:
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Method must be called on a dictionary',
            context
        ))
    
    if len(arguments) < 2:
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Missing argument: other',
            context
        ))
    
    if not isinstance(arguments[0], Dictionary):
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Type error: method must be called on a dictionary',
            context
        ))
    
    if not isinstance(arguments[1], Dictionary):
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Type error: first argument must be a dictionary',
            context
        ))

    dictionary = arguments[0].copy()
    other = arguments[1].copy()

    keys = map(lambda e: e.value, list(other.value.keys()))
    values = map(lambda e: e.value, list(other.value.values()))
    other_dictionary = dict(zip(keys, values))

    for key, value in dictionary.value.copy().items():
        if key.value in other_dictionary and other_dictionary[key.value] == value.value:
            del dictionary.value[key]

    return RuntimeResult().success(dictionary.set_context(context))

def Dictionary_remove(context, start_position, end_position, *arguments):
    if len(arguments) < 1:
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Method must be called on a dictionary',
            context
        ))
    
    if len(arguments) < 2:
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Missing argument: key',
            context
        ))
    
    if not isinstance(arguments[0], Dictionary):
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Type error: method must be called on a dictionary',
            context
        ))

    dictionary = arguments[0].copy()
    found = False

    for k, v in dictionary.value.items():
        key = k

        if key.value == arguments[1].value:
            found = True
            break

    if found:
        dictionary.value.pop(key)

    return RuntimeResult().success(dictionary.copy().set_context(context))

def Dictionary_remove_many(context, start_position, end_position, *arguments):
    if len(arguments) < 1:
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Method must be called on a dictionary',
            context
        ))
    
    if len(arguments) < 2:
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Missing argument: keys',
            context
        ))
    
    if not isinstance(arguments[0], Dictionary):
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Type error: method must be called on a dictionary',
            context
        ))
    
    if not isinstance(arguments[1], List):
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Type error: first argument must be a list',
            context
        ))
    
    dictionary = arguments[0].copy()
    keys = list(map(lambda e: e.value, arguments[1].value))

    for key, value in dictionary.value.copy().items():
        if key.value in keys:
            dictionary.value.pop(key)

    return RuntimeResult().success(dictionary.copy().set_context(context))

def Dictionary_add(context, start_position, end_position, *arguments):
    if len(arguments) < 1:
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Method must be called on a dictionary',
            context
        ))
    
    if len(arguments) < 2:
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Missing argument: key',
            context
        ))

    if len(arguments) < 3:
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Missing argument: value',
            context
        ))
    
    if not isinstance(arguments[0], Dictionary):
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Type error: method must be called on a dictionary',
            context
        ))

    dictionary = arguments[0].copy()
    key = arguments[1].copy().value
    value = arguments[2]

    for k, v in dictionary.value.items():
        if k.value == key:
            return RuntimeResult().failure(RuntimeError(
                start_position, end_position,
                'Key already exists: ' + key,
                context
            ))

    dictionary.value[get_value_from_object(key)] = value

    return RuntimeResult().success(dictionary.set_context(context))

def Dictionary_keys(context, start_position, end_position, *arguments):
    if len(arguments) < 1:
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Method must be called on a dictionary',
            context
        ))
    
    if not isinstance(arguments[0], Dictionary):
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Type error: method must be called on a dictionary',
            context
        ))

    dictionary = arguments[0].copy()
    keys = list(dictionary.value.keys())

    return RuntimeResult().success(List(keys).set_context(context))

def Dictionary_values(context, start_position, end_position, *arguments):
    if len(arguments) < 1:
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Method must be called on a dictionary',
            context
        ))
    
    if not isinstance(arguments[0], Dictionary):
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Type error: method must be called on a dictionary',
            context
        ))

    dictionary = arguments[0].copy()
    values = list(dictionary.value.values())
    
    return RuntimeResult().success(List(values).set_context(context))


def Text_strip(context, start_position, end_position, *arguments):
    if len(arguments) < 1:
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Method must be called on a text object',
            context
        ))
    
    if not isinstance(arguments[0], Text):
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Type error: method must be called on a text object',
            context
        ))
    
    return RuntimeResult().success(Text(arguments[0].value.strip()).set_context(context))

def Text_to_lowercase(context, start_position, end_position, *arguments):
    if len(arguments) < 1:
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Method must be called on a text object',
            context
        ))
    
    if not isinstance(arguments[0], Text):
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Type error: method must be called on a text object',
            context
        ))

    return RuntimeResult().success(Text(arguments[0].value.lower()).set_context(context))

def Text_to_uppercase(context, start_position, end_position, *arguments):
    if len(arguments) < 1:
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Method must be called on a text object',
            context
        ))
    
    if not isinstance(arguments[0], Text):
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Type error: method must be called on a text object',
            context
        ))

    return RuntimeResult().success(Text(arguments[0].value.upper()).set_context(context))

def Text_remove_suffix(context, start_position, end_position, *arguments):
    if len(arguments) < 1:
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Method must be called on a text object',
            context
        ))
    
    if len(arguments) < 2:
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Missing argument: suffix',
            context
        ))

    if not isinstance(arguments[0], Text):
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Type error: method must be called on a text object',
            context
        ))

    if not isinstance(arguments[1], Text):
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Type error: first argument must be a text object',
            context
        ))

    return RuntimeResult().success(Text(arguments[0].value.removesuffix(arguments[1].value)).set_context(context))

def Text_add_suffix(context, start_position, end_position, *arguments):
    if len(arguments) < 1:
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Method must be called on a text object',
            context
        ))
    
    if len(arguments) < 2:
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Missing argument: suffix',
            context
        ))

    if not isinstance(arguments[0], Text):
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Type error: method must be called on a text object',
            context
        ))

    if not isinstance(arguments[1], Text):
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Type error: first argument must be a text object',
            context
        ))

    return RuntimeResult().success(Text(arguments[0].value + arguments[1].value).set_context(context))

def Text_remove_prefix(context, start_position, end_position, *arguments):
    if len(arguments) < 1:
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Method must be called on a text object',
            context
        ))
    
    if len(arguments) < 2:
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Missing argument: prefix',
            context
        ))

    if not isinstance(arguments[0], Text):
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Type error: method must be called on a text object',
            context
        ))

    if not isinstance(arguments[1], Text):
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Type error: first argument must be a text object',
            context
        ))

    return RuntimeResult().success(Text(arguments[0].value.removeprefix(arguments[1].value)).set_context(context))

def Text_add_prefix(context, start_position, end_position, *arguments):
    if len(arguments) < 1:
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Method must be called on a text object',
            context
        ))
    
    if len(arguments) < 2:
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Missing argument: prefix',
            context
        ))

    if not isinstance(arguments[0], Text):
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Type error: method must be called on a text object',
            context
        ))

    if not isinstance(arguments[1], Text):
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Type error: first argument must be a text object',
            context
        ))

    return RuntimeResult().success(Text(arguments[1].value + arguments[0].value).set_context(context))

def dictionary_from_key_value_lists(context, start_position, end_position, *arguments):
    if len(arguments) < 1:
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Missing argument: keys',
            context
        ))
    
    if len(arguments) < 2:
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Missing argument: values',
            context
        ))

    if not isinstance(arguments[0], List):
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Type error: first argument must be a list',
            context
        ))

    if not isinstance(arguments[1], List):
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Type error: first argument must be a list',
            context
        ))
    
    if len(arguments[0].value) != len(arguments[1].value):
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Key and value lists must have the same length',
            context
        ))

    keys = arguments[0].value
    values = arguments[1].value
    dictionary = dict(zip(keys, values))

    return RuntimeResult().success(Dictionary(dictionary).set_context(context))

def is_defined(context, start_position, end_position, *arguments):
    if len(arguments) < 1:
        return RuntimeResult().failure(RuntimeError(
            start_position, end_position,
            'Missing argument: name',
            context
        ))

    name = arguments[0]
    defined = context.symbol_table.get(name) is not None
    return RuntimeResult().success(Number(float(defined)))

built_ins = {
    'print': print_value,
    'input': input_value,
    'length': length_of_value,
    'wait': sleep_value,
    'type': type_of_value,
    'Number': lambda context, start_position, end_position, *arguments: convert_value(context, start_position, end_position, 'to_number', *arguments),
    'Text': lambda context, start_position, end_position, *arguments: convert_value(context, start_position, end_position, 'to_text', *arguments),
    'List': lambda context, start_position, end_position, *arguments: RuntimeResult().success(List(*arguments).set_context(context)),
    'Dictionary': dictionary_from_key_value_lists,
    'BuiltIn': lambda context, start_position, end_position, *arguments: convert_value(context, start_position, end_position, 'to_built_in', *arguments),
    'Boolean': lambda context, start_position, end_position, *arguments: convert_value(context, start_position, end_position, 'to_boolean', *arguments),
    'Null': lambda context, start_position, end_position, *arguments: RuntimeResult().success(Null().set_context(context)),
    'List~append': List_append,
    'List~extend': List_extend,
    'List~remove': List_remove,
    'List~remove_all': List_remove_all,
    'List~subtract': List_subtract,
    'List~subtract_all': List_subtract_all,
    'List~contains': List_contains,
    'List~index_of': List_index_of,
    'List~insert': List_insert,
    'List~pop': List_pop,
    'List~count': List_count,
    'List~slice': List_slice,
    'List~map': List_map,
    'Dictionary~merge': Dictionary_merge,
    'Dictionary~difference': Dictionary_difference,
    'Dictionary~add': Dictionary_add,
    'Dictionary~remove': Dictionary_remove,
    'Dictionary~remove_many': Dictionary_remove_many,
    'Dictionary~keys': Dictionary_keys,
    'Dictionary~values': Dictionary_values,
    'Text~strip': Text_strip,
    'Text~to_lowercase': Text_to_lowercase,
    'Text~to_uppercase': Text_to_uppercase,
    'Text~remove_prefix': Text_remove_prefix,
    'Text~add_prefix': Text_add_prefix,
    'Text~remove_suffix': Text_remove_suffix,
    'Text~add_suffix': Text_add_suffix,
    'is_defined': is_defined
}

for key in built_ins:
    default_symbol_table.set(Text(key), BuiltIn(built_ins[key]).set_context(global_context))

## Copy default to global context

global_symbol_table = default_symbol_table.copy()
global_context.symbol_table = global_symbol_table

#endregion


#region INTERPRETER

class Interpreter():
    def visit(self, node, context: Context):
        method_name = f'visit_{type(node).__name__}'

        method = getattr(self, method_name, self.no_visit_method)
        return method(node, context)
    
    def no_visit_method(self, node, context: Context):
        raise NotImplementedError(f'No visit method was defined for {type(node).__name__}.')
    
    ## Visit Methods

    def visit_NumberNode(self, node: NumberNode, context: Context):
        return RuntimeResult().success(
            Number(node.token.value)
                .set_context(context)
                .set_position(node.start_position, node.end_position)
        )
    
    def visit_TextNode(self, node: TextNode, context: Context):
        return RuntimeResult().success(
            Text(node.token.value)
                .set_context(context)
                .set_position(node.start_position, node.end_position)
        )
    
    def visit_ListNode(self, node: ListNode, context: Context):
        result = RuntimeResult()
        elements = []

        for element_node in node.element_nodes:
            elements.append(result.register(self.visit(element_node, context)))
            if result.error: return result

        return result.success(
            List(elements)\
                .set_position(node.start_position, node.end_position)\
                .set_context(context)
        )
    
    def visit_DictionaryNode(self, node: DictionaryNode, context: Context):
        result = RuntimeResult()
        keys = []
        values = []

        for key_node in list(node.node_dictionary.keys()):
            keys.append(result.register(self.visit(key_node, context)))
            if result.error: return result

        for value_node in list(node.node_dictionary.values()):
            values.append(result.register(self.visit(value_node, context)))
            if result.error: return result

        return result.success(
            Dictionary(dict(zip(keys, values)))\
                .set_position(node.start_position, node.end_position)\
                .set_context(context)
        )

    def visit_BinaryOperationNode(self, node: BinaryOperationNode, context: Context):
        result = RuntimeResult()

        left = result.register(self.visit(node.left_node, context))
        if result.error: return result

        right = result.register(self.visit(node.right_node, context))
        if result.error: return result

        ## Arithmetic expressions
        if node.operator_token.type == TT_ADD:
            output = result.register(left.added_to(right))
        elif node.operator_token.type == TT_SUBTRACT:
            output = result.register(left.subtracted_by(right))
        elif node.operator_token.type == TT_MULIPLY:
            output = result.register(left.multiplied_by(right))
        elif node.operator_token.type == TT_DIVIDE:
            output = result.register(left.divided_by(right))
        elif node.operator_token.type == TT_POWER:
            output = result.register(left.powered_by(right))

        ## Comparaison expressions
        elif node.operator_token.type == TT_DOUBLE_EQUALS:
            output = result.register(left.is_equals_to(right))
        elif node.operator_token.type == TT_NOT_EQUALS:
            output = result.register(left.is_not_equals_to(right))
        elif node.operator_token.type == TT_GREATER_THAN:
            output = result.register(left.is_greater_than(right))
        elif node.operator_token.type == TT_LESS_THAN:
            output = result.register(left.is_less_than(right))
        elif node.operator_token.type == TT_GREATER_THAN_OR_EQUALS:
            output = result.register(left.is_greater_or_equals(right))
        elif node.operator_token.type == TT_LESS_THAN_OR_EQUALS:
            output = result.register(left.is_less_or_equals(right))

        ## Logical operators
        elif node.operator_token.matches(TT_KEYWORD, 'and'):
            output = result.register(left.and_(right))
        elif node.operator_token.matches(TT_KEYWORD, 'or'):
            output = result.register(left.or_(right))

        if result.error: return result
        
        return result.success(output
            .set_context(context)
            .set_position(node.start_position, node.end_position
        ))
    
    def visit_UnaryOperationNode(self, node: UnaryOperationNode, context: Context):
        result = RuntimeResult()

        number = result.register(self.visit(node.node, context))
        if result.error: return result

        if node.operation_token.type == TT_SUBTRACT:
            number = result.register(number.multiplied_by(Number(-1)))
        elif node.operation_token.matches(TT_KEYWORD, 'not'):
            number = result.register(number.not_())
        
        if result.error: return result
        
        return result.success(number
            .set_context(context)
            .set_position(node.start_position, node.end_position
        ))
    
    def visit_VariableNode(self, node: VariableNode, context: Context):
        result = RuntimeResult()

        variable_name = result.register(self.visit(node.variable_name_node, context))
        if result.error: return result

        scope_visit = result.register(self.visit(node.scope_node, context)) if node.scope_node else Number(0)
        if result.error: return result

        if isinstance(scope_visit, Number):
            if scope_visit.value < 0:
                return result.failure(RuntimeError(
                    node.start_position, node.scope_node.end_position.copy().advance(),
                    "Can't access scope from a negative number",
                    context
                ))
            
            if not scope_visit.value.is_integer():
                return result.failure(RuntimeError(
                    node.start_position, node.scope_node.end_position.copy().advance(),
                    "Can't access scope from a decimal number",
                    context
                ))

            scope = context.symbol_table

            for _ in range(int(scope_visit.value)):
                scope = scope.parent

                if not scope:
                    return result.failure(RuntimeError(
                        node.start_position, node.scope_node.end_position.copy().advance(),
                        "Scope is out of range",
                        context
                    ))
                
        elif isinstance(scope_visit, SymbolTable):
            scope = scope_visit

        return result.success((variable_name, scope, node.scope_node is not None))
    
    def visit_VariableAccessNode(self, node: VariableAccessNode, context: Context):
        result = RuntimeResult()

        variable_data = result.register(self.visit(node.variable_node, context))
        if result.error: return result

        variable_name, scope, explicit = variable_data
        value = scope.get(variable_name, explicit)

        if not value:
            return result.failure(RuntimeError(
                node.start_position, node.end_position,
                f"Variable '{variable_name}' is not defined.",
                context
            ))

        value = value.copy().set_position(node.start_position, node.end_position) # Fix position for error messages
        return result.success(value)
    
    def visit_VariableAssignmentNode(self, node: VariableAssignmentNode, context: Context):
        result = RuntimeResult()
        
        variable_data = result.register(self.visit(node.variable_node, context))
        if result.error: return result

        variable_name, scope, explicit = variable_data

        value = result.register(self.visit(node.value_node, context))
        if result.error: return result

        if explicit:
            scope.set(variable_name, value)
        else:
            levels_up = 0
            current_table = context.symbol_table

            while True:
                if current_table.parent is None:
                    levels_up = 0
                    current_table = context.symbol_table
                    break

                levels_up += 1
                current_table = current_table.parent

                if current_table.get(variable_name) is not None:
                    break

            current_table.set(variable_name, value)

        return(result.success(value))
    
    def visit_CallNode(self, node: CallNode, context: Context):
        result = RuntimeResult()
        arguments = []

        value_to_call = result.register(self.visit(node.node_to_call, context))
        if result.error: return result

        value_to_call = value_to_call.copy().set_position(node.start_position, node.end_position)

        for argument_node in node.argument_nodes:
            arguments.append(result.register(self.visit(argument_node, context)))
            if result.error: return result

        return_value = result.register(value_to_call.execute(arguments))
        if result.error: return result

        return result.success(return_value)
    
    def visit_IndexingNode(self, node: IndexingNode, context: Context):
        result = RuntimeResult()

        base_value = result.register(self.visit(node.base_node, context))
        if result.error: return result

        index_value = result.register(self.visit(node.index_node, context))
        if result.error: return result

        if node.allow_methods:
            method_name = type(base_value).__name__ + "~" + str(index_value)
            function = context.symbol_table.get(Text(method_name))

            if isinstance(function, (BuiltIn, Text)):
                function.base_value = base_value
                return result.success(function)

        index_result = result.register(base_value.index(index_value))
        if result.error: return result

        return result.success(index_result.set_context(index_value.context))
    
    def visit_IndexAssignmentNode(self, node: IndexAssignmentNode, context: Context):
        result = RuntimeResult()

        base_value = result.register(self.visit(node.indexing_node.base_node, context))
        if result.error: return result

        index_value = result.register(self.visit(node.indexing_node.index_node, context))
        if result.error: return result

        value_value = result.register(self.visit(node.value_node, context))
        if result.error: return result

        output_value = result.register(base_value.assign_index(index_value, value_value))
        if result.error: return result

        variable_node = node.variable_node
        assignment_node = VariableAssignmentNode(variable_node, ValueNode(output_value))

        result.register(self.visit(assignment_node, context))
        if result.error: return result

        return result.success(Null().set_context(index_value.context))

    def visit_ValueNode(self, node: ValueNode, context: Context):
        return RuntimeResult().success(node.value)

    def visit_NullNode(self, node: NullNode, context: Context):
        return RuntimeResult().success(Null())

    def visit_GlobalScopeNode(self, node: GlobalScopeNode, context: Context):
        return RuntimeResult().success(global_symbol_table)
    
    def visit_DefaultScopeNode(self, node: GlobalScopeNode, context: Context):
        return RuntimeResult().success(default_symbol_table)

    def visit_IfNode(self, node: IfNode, context: Context):
        result = RuntimeResult()

        condition = result.register(self.visit(node.condition_node, context))
        if result.error: return result

        condition_boolean = result.register(condition.to_boolean())
        if result.error: return result

        if condition_boolean.value == 1:
            value_to_call = result.register(self.visit(node.true_node, context))
            if result.error: return result

            return_result = result.register(value_to_call.execute([]))
            if result.error: return result

            return result.success(return_result)
        
        if condition_boolean.value == 0 and node.false_node is not None:
            value_to_call = result.register(self.visit(node.false_node, context))
            if result.error: return result

            if isinstance(node.false_node, IfNode):
                return result.success(value_to_call.set_context(context))

            return_result = result.register(value_to_call.execute([]))
            if result.error: return result

            return result.success(return_result)

        return result.success(Null().set_context(context))
    
    def visit_WhileNode(self, node: WhileNode, context: Context):
        result = RuntimeResult()

        while True:
            condition = result.register(self.visit(node.condition_node, context))
            if result.error: return result

            condition_boolean = result.register(condition.to_boolean())
            if result.error: return result

            if condition_boolean.value == 1:
                value_to_call = result.register(self.visit(node.while_node, context))
                if result.error: return result

                result.register(value_to_call.execute([]))
                if result.error: return result            
            else:
                break

        return result.success(Null().set_context(context))
    
#endregion


#region RUN

def make_tokens(file_name: str, text: str) -> list[Token]:
    lexer = Lexer(file_name, text)
    tokens, error = lexer.make_tokens()

    return tokens, error

def generate_ast(tokens: list[Token]) -> ParseResult:
    parser = Parser(tokens)
    ast = parser.parse()

    return ast

def interpret_ast(ast: Node, context: Context = global_context):
    interpreter = Interpreter()

    result = interpreter.visit(ast.node, context if context else global_context)
    return result


def run(file_name, text, context: Context = global_context):
    tokens, error = make_tokens(file_name, text)
    if error: return None, error

    ast = generate_ast(tokens)
    if ast.error: return None, ast.error

    result = interpret_ast(ast, context)
    return result.value, result.error

#endregion






