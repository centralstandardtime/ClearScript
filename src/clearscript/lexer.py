"""
Lexer for ClearScript

Tokenizes ClearScript source code into a stream of tokens.
"""

import re
from enum import Enum, auto
from dataclasses import dataclass
from typing import List, Optional


class TokenType(Enum):
    """Token types for ClearScript."""
    # Keywords
    INT = auto()
    FLOAT = auto()
    FUNCTION = auto()
    GOTO = auto()
    LABEL = auto()
    DO = auto()
    IN = auto()
    IF = auto()
    ELSE = auto()
    WHILE = auto()
    RETURN = auto()
    
    # StateScript commands
    WAIT = auto()
    WAITFOR = auto()
    KILL = auto()
    THREAD = auto()
    SET = auto()
    PUSH = auto()
    POP = auto()
    PEEK = auto()
    
    # Built-in functions (as keywords for easier parsing)
    SPAWNBOT = auto()
    MOVETO = auto()
    ANIMATE = auto()
    DELETE = auto()
    
    # OOP and advanced features
    CLASS = auto()
    STRUCT = auto()
    METHOD = auto()
    THIS = auto()
    NEW = auto()
    
    # Control flow extensions
    FOR = auto()
    SWITCH = auto()
    CASE = auto()
    BREAK = auto()
    DEFAULT = auto()
    
    # Utilities
    CONST = auto()
    ENUM = auto()
    AUTO = auto()
    
    # Special
    RAW = auto()  # For raw StateScript blocks
    
    # Identifiers and literals
    IDENTIFIER = auto()
    NUMBER = auto()
    STRING = auto()
    
    # Operators
    PLUS = auto()
    MINUS = auto()
    MULTIPLY = auto()
    DIVIDE = auto()
    ASSIGN = auto()
    EQ = auto()           # ==
    NEQ = auto()          # !=
    LT = auto()           # <
    GT = auto()           # >
    LTE = auto()          # <=
    GTE = auto()          # >=
    AND = auto()          # &&
    OR = auto()           # ||
    NOT = auto()          # !
    INCREMENT = auto()    # ++
    DECREMENT = auto()    # --
    
    # Delimiters
    LPAREN = auto()
    RPAREN = auto()
    LBRACE = auto()
    RBRACE = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    SEMICOLON = auto()
    COMMA = auto()
    COLON = auto()
    DOT = auto()          # .
    QUESTION = auto()     # ?
    
    # Special
    COMMENT = auto()
    NEWLINE = auto()
    EOF = auto()


@dataclass
class Token:
    """Represents a single token."""
    type: TokenType
    value: any
    line: int
    column: int
    
    def __repr__(self):
        return f"Token({self.type.name}, {repr(self.value)}, {self.line}:{self.column})"


class Lexer:
    """Lexical analyzer for ClearScript."""
    
    KEYWORDS = {
        'int': TokenType.INT,
        'float': TokenType.FLOAT,
        'function': TokenType.FUNCTION,
        'goto': TokenType.GOTO,
        'label': TokenType.LABEL,
        'do': TokenType.DO,
        'in': TokenType.IN,
        'if': TokenType.IF,
        'else': TokenType.ELSE,
        'while': TokenType.WHILE,
        'return': TokenType.RETURN,
        'wait': TokenType.WAIT,
        'waitfor': TokenType.WAITFOR,
        'kill': TokenType.KILL,
        'thread': TokenType.THREAD,
        'set': TokenType.SET,
        'push': TokenType.PUSH,
        'pop': TokenType.POP,
        'peek': TokenType.PEEK,
        'spawnbot': TokenType.SPAWNBOT,
        'moveto': TokenType.MOVETO,
        'animate': TokenType.ANIMATE,
        'delete': TokenType.DELETE,
        'raw': TokenType.RAW,
        'class': TokenType.CLASS,
        'struct': TokenType.STRUCT,
        'method': TokenType.METHOD,
        'this': TokenType.THIS,
        'new': TokenType.NEW,
        'for': TokenType.FOR,
        'switch': TokenType.SWITCH,
        'case': TokenType.CASE,
        'break': TokenType.BREAK,
        'default': TokenType.DEFAULT,
        'const': TokenType.CONST,
        'enum': TokenType.ENUM,
        'auto': TokenType.AUTO,
    }
    
    def __init__(self, source: str):
        """Initialize the lexer with source code."""
        self.source = source
        self.pos = 0
        self.line = 1
        self.column = 1
        self.tokens: List[Token] = []
    
    def current_char(self) -> Optional[str]:
        """Get the current character without advancing."""
        if self.pos >= len(self.source):
            return None
        return self.source[self.pos]
    
    def peek_char(self, offset: int = 1) -> Optional[str]:
        """Peek ahead at a character."""
        pos = self.pos + offset
        if pos >= len(self.source):
            return None
        return self.source[pos]
    
    def advance(self) -> Optional[str]:
        """Consume and return the current character."""
        if self.pos >= len(self.source):
            return None
        
        char = self.source[self.pos]
        self.pos += 1
        
        if char == '\n':
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        
        return char
    
    def skip_whitespace(self):
        """Skip whitespace characters (except newlines in some contexts)."""
        while self.current_char() and self.current_char() in ' \t\r\n':
            self.advance()
    
    def read_line_comment(self) -> str:
        """Read a line comment starting with //"""
        comment = ""
        self.advance()  # Skip first /
        self.advance()  # Skip second /
        
        while self.current_char() and self.current_char() != '\n':
            comment += self.current_char()
            self.advance()
        
        return comment.strip()
    
    def read_block_comment(self) -> str:
        """Read a block comment /* ... */"""
        comment = ""
        self.advance()  # Skip /
        self.advance()  # Skip *
        
        while True:
            if self.current_char() is None:
                raise SyntaxError(f"Unterminated block comment at {self.line}:{self.column}")
            
            if self.current_char() == '*' and self.peek_char() == '/':
                self.advance()  # Skip *
                self.advance()  # Skip /
                break
            
            comment += self.current_char()
            self.advance()
        
        return comment.strip()
    
    def read_number(self) -> Token:
        """Read a numeric literal."""
        start_line = self.line
        start_column = self.column
        num_str = ""
        
        while self.current_char() and (self.current_char().isdigit() or self.current_char() == '.'):
            num_str += self.current_char()
            self.advance()
        
        # Determine if int or float
        if '.' in num_str:
            value = float(num_str)
        else:
            value = int(num_str)
        
        return Token(TokenType.NUMBER, value, start_line, start_column)
    
    def read_identifier(self) -> Token:
        """Read an identifier or keyword."""
        start_line = self.line
        start_column = self.column
        ident = ""
        
        while self.current_char() and (self.current_char().isalnum() or self.current_char() == '_'):
            ident += self.current_char()
            self.advance()
        
        # Check if it's a keyword
        token_type = self.KEYWORDS.get(ident, TokenType.IDENTIFIER)
        
        return Token(token_type, ident, start_line, start_column)
    
    def read_string(self) -> Token:
        """Read a string literal."""
        start_line = self.line
        start_column = self.column
        quote_char = self.current_char()  # ' or "
        self.advance()  # Skip opening quote
        
        string = ""
        while self.current_char() and self.current_char() != quote_char:
            if self.current_char() == '\\':
                self.advance()
                # Handle escape sequences
                escape_char = self.current_char()
                if escape_char == 'n':
                    string += '\n'
                elif escape_char == 't':
                    string += '\t'
                elif escape_char == '\\':
                    string += '\\'
                elif escape_char == quote_char:
                    string += quote_char
                else:
                    string += escape_char
                self.advance()
            else:
                string += self.current_char()
                self.advance()
        
        if self.current_char() != quote_char:
            raise SyntaxError(f"Unterminated string at {start_line}:{start_column}")
        
        self.advance()  # Skip closing quote
        return Token(TokenType.STRING, string, start_line, start_column)
    
    def tokenize(self) -> List[Token]:
        """Tokenize the entire source code."""
        self.tokens = []
        
        while self.pos < len(self.source):
            self.skip_whitespace()
            
            if self.current_char() is None:
                break
            
            start_line = self.line
            start_column = self.column
            char = self.current_char()
            
            # Comments
            if char == '/' and self.peek_char() == '/':
                comment = self.read_line_comment()
                self.tokens.append(Token(TokenType.COMMENT, comment, start_line, start_column))
                continue
            
            if char == '/' and self.peek_char() == '*':
                comment = self.read_block_comment()
                self.tokens.append(Token(TokenType.COMMENT, comment, start_line, start_column))
                continue
            
            # Numbers
            if char.isdigit():
                self.tokens.append(self.read_number())
                continue
            
            # Identifiers and keywords
            if char.isalpha() or char == '_':
                self.tokens.append(self.read_identifier())
                continue
            
            # Strings
            if char in '"\'':
                self.tokens.append(self.read_string())
                continue
            
            # Two-character operators
            if char == '=' and self.peek_char() == '=':
                self.advance()
                self.advance()
                self.tokens.append(Token(TokenType.EQ, '==', start_line, start_column))
                continue
            
            if char == '!' and self.peek_char() == '=':
                self.advance()
                self.advance()
                self.tokens.append(Token(TokenType.NEQ, '!=', start_line, start_column))
                continue
            
            if char == '<' and self.peek_char() == '=':
                self.advance()
                self.advance()
                self.tokens.append(Token(TokenType.LTE, '<=', start_line, start_column))
                continue
            
            if char == '>' and self.peek_char() == '=':
                self.advance()
                self.advance()
                self.tokens.append(Token(TokenType.GTE, '>=', start_line, start_column))
                continue
            
            if char == '&' and self.peek_char() == '&':
                self.advance()
                self.advance()
                self.tokens.append(Token(TokenType.AND, '&&', start_line, start_column))
                continue
            
            if char == '|' and self.peek_char() == '|':
                self.advance()
                self.advance()
                self.tokens.append(Token(TokenType.OR, '||', start_line, start_column))
                continue
            
            if char == '+' and self.peek_char() == '+':
                self.advance()
                self.advance()
                self.tokens.append(Token(TokenType.INCREMENT, '++', start_line, start_column))
                continue
            
            if char == '-' and self.peek_char() == '-':
                self.advance()
                self.advance()
                self.tokens.append(Token(TokenType.DECREMENT, '--', start_line, start_column))
                continue
            
            # Single-character tokens
            single_char_tokens = {
                '+': TokenType.PLUS,
                '-': TokenType.MINUS,
                '*': TokenType.MULTIPLY,
                '/': TokenType.DIVIDE,
                '=': TokenType.ASSIGN,
                '<': TokenType.LT,
                '>': TokenType.GT,
                '!': TokenType.NOT,
                '(': TokenType.LPAREN,
                ')': TokenType.RPAREN,
                '{': TokenType.LBRACE,
                '}': TokenType.RBRACE,
                '[': TokenType.LBRACKET,
                ']': TokenType.RBRACKET,
                ';': TokenType.SEMICOLON,
                ',': TokenType.COMMA,
                ':': TokenType.COLON,
                '.': TokenType.DOT,
                '?': TokenType.QUESTION,
            }
            
            if char in single_char_tokens:
                self.advance()
                self.tokens.append(Token(single_char_tokens[char], char, start_line, start_column))
                continue
            
            # Unknown character
            raise SyntaxError(f"Unexpected character '{char}' at {start_line}:{start_column}")
        
        # Add EOF token
        self.tokens.append(Token(TokenType.EOF, None, self.line, self.column))
        return self.tokens
