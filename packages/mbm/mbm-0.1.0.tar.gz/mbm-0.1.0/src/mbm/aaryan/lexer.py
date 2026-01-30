"""
Aaryan Language Lexer

Tokenizes Aaryan source code into tokens for parsing.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional, Iterator


class TokenType(Enum):
    """Token types for the Aaryan language."""
    
    # Literals
    NUMBER = auto()
    STRING = auto()
    IDENTIFIER = auto()
    BOOLEAN = auto()
    
    # Keywords
    LET = auto()
    CONST = auto()
    FN = auto()
    IF = auto()
    ELSE = auto()
    WHILE = auto()
    FOR = auto()
    RETURN = auto()
    PRINT = auto()
    TRUE = auto()
    FALSE = auto()
    NULL = auto()
    AND = auto()
    OR = auto()
    NOT = auto()
    
    # Operators
    PLUS = auto()
    MINUS = auto()
    MULTIPLY = auto()
    DIVIDE = auto()
    MODULO = auto()
    ASSIGN = auto()
    EQUALS = auto()
    NOT_EQUALS = auto()
    LESS_THAN = auto()
    GREATER_THAN = auto()
    LESS_EQUAL = auto()
    GREATER_EQUAL = auto()
    
    # Delimiters
    LPAREN = auto()
    RPAREN = auto()
    LBRACE = auto()
    RBRACE = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    COMMA = auto()
    SEMICOLON = auto()
    COLON = auto()
    DOT = auto()
    
    # Special
    NEWLINE = auto()
    EOF = auto()
    COMMENT = auto()


@dataclass
class Token:
    """Represents a single token."""
    
    type: TokenType
    value: str
    line: int
    column: int
    
    def __str__(self) -> str:
        return f"Token({self.type.name}, {self.value!r}, line={self.line})"


class Lexer:
    """
    Lexer for the Aaryan language.
    
    Converts source code text into a stream of tokens.
    """
    
    # Keyword mapping
    KEYWORDS = {
        'let': TokenType.LET,
        'const': TokenType.CONST,
        'fn': TokenType.FN,
        'if': TokenType.IF,
        'else': TokenType.ELSE,
        'while': TokenType.WHILE,
        'for': TokenType.FOR,
        'return': TokenType.RETURN,
        'print': TokenType.PRINT,
        'true': TokenType.TRUE,
        'false': TokenType.FALSE,
        'null': TokenType.NULL,
        'and': TokenType.AND,
        'or': TokenType.OR,
        'not': TokenType.NOT,
    }
    
    def __init__(self, source: str):
        """
        Initialize lexer with source code.
        
        Args:
            source: Source code to tokenize
        """
        self.source = source
        self.pos = 0
        self.line = 1
        self.column = 1
        self.tokens: list[Token] = []
    
    @property
    def current_char(self) -> Optional[str]:
        """Get the current character."""
        if self.pos < len(self.source):
            return self.source[self.pos]
        return None
    
    @property
    def next_char(self) -> Optional[str]:
        """Peek at the next character."""
        if self.pos + 1 < len(self.source):
            return self.source[self.pos + 1]
        return None
    
    def advance(self) -> Optional[str]:
        """Move to the next character."""
        char = self.current_char
        self.pos += 1
        
        if char == '\n':
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        
        return char
    
    def skip_whitespace(self) -> None:
        """Skip whitespace characters (except newlines)."""
        while self.current_char and self.current_char in ' \t\r':
            self.advance()
    
    def skip_comment(self) -> None:
        """Skip single-line comments starting with #."""
        while self.current_char and self.current_char != '\n':
            self.advance()
    
    def read_string(self, quote_char: str) -> Token:
        """Read a string literal."""
        start_line = self.line
        start_col = self.column
        
        self.advance()  # Skip opening quote
        value = ""
        
        while self.current_char and self.current_char != quote_char:
            if self.current_char == '\\':
                self.advance()
                # Handle escape sequences
                if self.current_char == 'n':
                    value += '\n'
                elif self.current_char == 't':
                    value += '\t'
                elif self.current_char == '\\':
                    value += '\\'
                elif self.current_char == quote_char:
                    value += quote_char
                else:
                    value += self.current_char or ''
                self.advance()
            else:
                value += self.current_char
                self.advance()
        
        self.advance()  # Skip closing quote
        
        return Token(TokenType.STRING, value, start_line, start_col)
    
    def read_number(self) -> Token:
        """Read a number literal."""
        start_line = self.line
        start_col = self.column
        value = ""
        
        # Integer part
        while self.current_char and self.current_char.isdigit():
            value += self.current_char
            self.advance()
        
        # Decimal part
        if self.current_char == '.' and self.next_char and self.next_char.isdigit():
            value += self.advance()  # Add '.'
            while self.current_char and self.current_char.isdigit():
                value += self.current_char
                self.advance()
        
        return Token(TokenType.NUMBER, value, start_line, start_col)
    
    def read_identifier(self) -> Token:
        """Read an identifier or keyword."""
        start_line = self.line
        start_col = self.column
        value = ""
        
        while self.current_char and (self.current_char.isalnum() or self.current_char == '_'):
            value += self.current_char
            self.advance()
        
        # Check if it's a keyword
        token_type = self.KEYWORDS.get(value.lower(), TokenType.IDENTIFIER)
        
        # Handle boolean literals
        if token_type == TokenType.TRUE or token_type == TokenType.FALSE:
            token_type = TokenType.BOOLEAN
        
        return Token(token_type, value, start_line, start_col)
    
    def make_token(self, token_type: TokenType, value: str = None) -> Token:
        """Create a token at the current position."""
        token = Token(
            token_type,
            value or self.current_char or '',
            self.line,
            self.column,
        )
        self.advance()
        return token
    
    def tokenize(self) -> list[Token]:
        """
        Tokenize the entire source code.
        
        Returns:
            List of tokens
        """
        self.tokens = []
        
        while self.current_char:
            # Skip whitespace
            if self.current_char in ' \t\r':
                self.skip_whitespace()
                continue
            
            # Newline
            if self.current_char == '\n':
                self.tokens.append(self.make_token(TokenType.NEWLINE, '\\n'))
                continue
            
            # Comment
            if self.current_char == '#':
                self.skip_comment()
                continue
            
            # String
            if self.current_char in '"\'':
                self.tokens.append(self.read_string(self.current_char))
                continue
            
            # Number
            if self.current_char.isdigit():
                self.tokens.append(self.read_number())
                continue
            
            # Identifier or keyword
            if self.current_char.isalpha() or self.current_char == '_':
                self.tokens.append(self.read_identifier())
                continue
            
            # Two-character operators
            if self.current_char == '=' and self.next_char == '=':
                token = Token(TokenType.EQUALS, '==', self.line, self.column)
                self.advance()
                self.advance()
                self.tokens.append(token)
                continue
            
            if self.current_char == '!' and self.next_char == '=':
                token = Token(TokenType.NOT_EQUALS, '!=', self.line, self.column)
                self.advance()
                self.advance()
                self.tokens.append(token)
                continue
            
            if self.current_char == '<' and self.next_char == '=':
                token = Token(TokenType.LESS_EQUAL, '<=', self.line, self.column)
                self.advance()
                self.advance()
                self.tokens.append(token)
                continue
            
            if self.current_char == '>' and self.next_char == '=':
                token = Token(TokenType.GREATER_EQUAL, '>=', self.line, self.column)
                self.advance()
                self.advance()
                self.tokens.append(token)
                continue
            
            # Single-character tokens
            single_char_tokens = {
                '+': TokenType.PLUS,
                '-': TokenType.MINUS,
                '*': TokenType.MULTIPLY,
                '/': TokenType.DIVIDE,
                '%': TokenType.MODULO,
                '=': TokenType.ASSIGN,
                '<': TokenType.LESS_THAN,
                '>': TokenType.GREATER_THAN,
                '(': TokenType.LPAREN,
                ')': TokenType.RPAREN,
                '{': TokenType.LBRACE,
                '}': TokenType.RBRACE,
                '[': TokenType.LBRACKET,
                ']': TokenType.RBRACKET,
                ',': TokenType.COMMA,
                ';': TokenType.SEMICOLON,
                ':': TokenType.COLON,
                '.': TokenType.DOT,
            }
            
            if self.current_char in single_char_tokens:
                self.tokens.append(self.make_token(single_char_tokens[self.current_char]))
                continue
            
            # Unknown character - skip with warning
            self.advance()
        
        # Add EOF token
        self.tokens.append(Token(TokenType.EOF, '', self.line, self.column))
        
        return self.tokens
    
    def __iter__(self) -> Iterator[Token]:
        """Iterate over tokens."""
        if not self.tokens:
            self.tokenize()
        return iter(self.tokens)
