"""
Aaryan Language Parser

Parses tokens into an Abstract Syntax Tree (AST).
"""

from __future__ import annotations

from typing import Optional

from mbm.aaryan.lexer import Lexer, Token, TokenType
from mbm.aaryan.ast import (
    ASTNode, Program, NumberLiteral, StringLiteral, BooleanLiteral,
    NullLiteral, Identifier, BinaryOp, UnaryOp, FunctionCall,
    ArrayLiteral, IndexAccess, ExpressionStatement, VariableDeclaration,
    Assignment, PrintStatement, Block, IfStatement, WhileStatement,
    ForStatement, FunctionDeclaration, ReturnStatement,
)
from mbm.core.exceptions import ParseError


class Parser:
    """
    Parser for the Aaryan language.
    
    Uses recursive descent parsing to build an AST from tokens.
    """
    
    def __init__(self, tokens: list[Token] = None):
        """
        Initialize parser.
        
        Args:
            tokens: List of tokens to parse
        """
        self.tokens = tokens or []
        self.pos = 0
        self.errors: list[str] = []
    
    @property
    def current(self) -> Optional[Token]:
        """Get current token."""
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None
    
    @property
    def previous(self) -> Optional[Token]:
        """Get previous token."""
        if self.pos > 0:
            return self.tokens[self.pos - 1]
        return None
    
    def peek(self, offset: int = 0) -> Optional[Token]:
        """Peek at a token at the given offset."""
        index = self.pos + offset
        if 0 <= index < len(self.tokens):
            return self.tokens[index]
        return None
    
    def advance(self) -> Optional[Token]:
        """Advance to the next token."""
        token = self.current
        if self.pos < len(self.tokens):
            self.pos += 1
        return token
    
    def match(self, *types: TokenType) -> bool:
        """Check if current token matches any of the given types."""
        if self.current and self.current.type in types:
            self.advance()
            return True
        return False
    
    def check(self, token_type: TokenType) -> bool:
        """Check current token type without advancing."""
        return self.current and self.current.type == token_type
    
    def expect(self, token_type: TokenType, message: str = None) -> Token:
        """Expect a specific token type or raise error."""
        if self.check(token_type):
            return self.advance()
        
        msg = message or f"Expected {token_type.name}"
        if self.current:
            msg += f", got {self.current.type.name}"
            raise ParseError(msg, self.current.line, self.current.column)
        raise ParseError(msg)
    
    def skip_newlines(self) -> None:
        """Skip newline tokens."""
        while self.match(TokenType.NEWLINE):
            pass
    
    def parse(self, source: str = None) -> Program:
        """
        Parse source code into an AST.
        
        Args:
            source: Source code string (optional if tokens already set)
            
        Returns:
            Program AST node
        """
        if source:
            lexer = Lexer(source)
            self.tokens = lexer.tokenize()
            self.pos = 0
        
        self.errors = []
        statements = []
        
        self.skip_newlines()
        
        while self.current and self.current.type != TokenType.EOF:
            try:
                stmt = self.parse_statement()
                if stmt:
                    statements.append(stmt)
            except ParseError as e:
                self.errors.append(str(e))
                self.synchronize()
            
            self.skip_newlines()
        
        return Program(statements=statements)
    
    def synchronize(self) -> None:
        """Recover from parse error by advancing to next statement."""
        self.advance()
        
        while self.current and self.current.type != TokenType.EOF:
            if self.previous and self.previous.type == TokenType.NEWLINE:
                return
            
            if self.current.type in (
                TokenType.LET, TokenType.CONST, TokenType.FN,
                TokenType.IF, TokenType.WHILE, TokenType.FOR,
                TokenType.RETURN, TokenType.PRINT,
            ):
                return
            
            self.advance()
    
    def parse_statement(self) -> Optional[ASTNode]:
        """Parse a single statement."""
        self.skip_newlines()
        
        if not self.current or self.current.type == TokenType.EOF:
            return None
        
        # Variable declaration
        if self.match(TokenType.LET):
            return self.parse_variable_declaration(is_const=False)
        
        if self.match(TokenType.CONST):
            return self.parse_variable_declaration(is_const=True)
        
        # Function declaration
        if self.match(TokenType.FN):
            return self.parse_function_declaration()
        
        # Control flow
        if self.match(TokenType.IF):
            return self.parse_if_statement()
        
        if self.match(TokenType.WHILE):
            return self.parse_while_statement()
        
        if self.match(TokenType.FOR):
            return self.parse_for_statement()
        
        if self.match(TokenType.RETURN):
            return self.parse_return_statement()
        
        # Print statement
        if self.match(TokenType.PRINT):
            return self.parse_print_statement()
        
        # Block
        if self.match(TokenType.LBRACE):
            return self.parse_block()
        
        # Expression statement
        return self.parse_expression_statement()
    
    def parse_variable_declaration(self, is_const: bool) -> VariableDeclaration:
        """Parse let/const declaration."""
        name_token = self.expect(TokenType.IDENTIFIER, "Expected variable name")
        
        value = None
        if self.match(TokenType.ASSIGN):
            value = self.parse_expression()
        
        return VariableDeclaration(
            name=name_token.value,
            value=value,
            is_const=is_const,
            line=name_token.line,
            column=name_token.column,
        )
    
    def parse_function_declaration(self) -> FunctionDeclaration:
        """Parse function declaration."""
        name_token = self.expect(TokenType.IDENTIFIER, "Expected function name")
        
        self.expect(TokenType.LPAREN, "Expected '(' after function name")
        
        parameters = []
        if not self.check(TokenType.RPAREN):
            parameters.append(self.expect(TokenType.IDENTIFIER).value)
            while self.match(TokenType.COMMA):
                parameters.append(self.expect(TokenType.IDENTIFIER).value)
        
        self.expect(TokenType.RPAREN, "Expected ')' after parameters")
        
        self.skip_newlines()
        self.expect(TokenType.LBRACE, "Expected '{' before function body")
        body = self.parse_block()
        
        return FunctionDeclaration(
            name=name_token.value,
            parameters=parameters,
            body=body,
            line=name_token.line,
            column=name_token.column,
        )
    
    def parse_if_statement(self) -> IfStatement:
        """Parse if/else statement."""
        line = self.previous.line
        column = self.previous.column
        
        condition = self.parse_expression()
        
        self.skip_newlines()
        self.expect(TokenType.LBRACE, "Expected '{' after if condition")
        then_branch = self.parse_block()
        
        else_branch = None
        self.skip_newlines()
        if self.match(TokenType.ELSE):
            self.skip_newlines()
            if self.match(TokenType.IF):
                else_branch = self.parse_if_statement()
            else:
                self.expect(TokenType.LBRACE, "Expected '{' after else")
                else_branch = self.parse_block()
        
        return IfStatement(
            condition=condition,
            then_branch=then_branch,
            else_branch=else_branch,
            line=line,
            column=column,
        )
    
    def parse_while_statement(self) -> WhileStatement:
        """Parse while loop."""
        line = self.previous.line
        column = self.previous.column
        
        condition = self.parse_expression()
        
        self.skip_newlines()
        self.expect(TokenType.LBRACE, "Expected '{' after while condition")
        body = self.parse_block()
        
        return WhileStatement(
            condition=condition,
            body=body,
            line=line,
            column=column,
        )
    
    def parse_for_statement(self) -> ForStatement:
        """Parse for loop."""
        line = self.previous.line
        column = self.previous.column
        
        var_token = self.expect(TokenType.IDENTIFIER, "Expected variable name")
        self.expect(TokenType.IDENTIFIER, "Expected 'in' keyword")  # 'in'
        iterable = self.parse_expression()
        
        self.skip_newlines()
        self.expect(TokenType.LBRACE, "Expected '{' after for header")
        body = self.parse_block()
        
        return ForStatement(
            variable=var_token.value,
            iterable=iterable,
            body=body,
            line=line,
            column=column,
        )
    
    def parse_return_statement(self) -> ReturnStatement:
        """Parse return statement."""
        line = self.previous.line
        column = self.previous.column
        
        value = None
        if not self.check(TokenType.NEWLINE) and not self.check(TokenType.RBRACE):
            value = self.parse_expression()
        
        return ReturnStatement(value=value, line=line, column=column)
    
    def parse_print_statement(self) -> PrintStatement:
        """Parse print statement."""
        line = self.previous.line
        column = self.previous.column
        
        expression = self.parse_expression()
        
        return PrintStatement(expression=expression, line=line, column=column)
    
    def parse_block(self) -> Block:
        """Parse a block of statements."""
        line = self.previous.line if self.previous else 1
        column = self.previous.column if self.previous else 1
        
        statements = []
        self.skip_newlines()
        
        while not self.check(TokenType.RBRACE) and not self.check(TokenType.EOF):
            stmt = self.parse_statement()
            if stmt:
                statements.append(stmt)
            self.skip_newlines()
        
        self.expect(TokenType.RBRACE, "Expected '}'")
        
        return Block(statements=statements, line=line, column=column)
    
    def parse_expression_statement(self) -> Optional[ExpressionStatement]:
        """Parse expression as statement."""
        expr = self.parse_expression()
        
        if not expr:
            return None
        
        # Check for assignment
        if isinstance(expr, Identifier) and self.match(TokenType.ASSIGN):
            value = self.parse_expression()
            return Assignment(
                name=expr.name,
                value=value,
                line=expr.line,
                column=expr.column,
            )
        
        return ExpressionStatement(
            expression=expr,
            line=expr.line,
            column=expr.column,
        )
    
    def parse_expression(self) -> Optional[ASTNode]:
        """Parse an expression."""
        return self.parse_or()
    
    def parse_or(self) -> Optional[ASTNode]:
        """Parse logical OR."""
        expr = self.parse_and()
        
        while self.match(TokenType.OR):
            operator = self.previous.value
            right = self.parse_and()
            expr = BinaryOp(
                left=expr,
                operator=operator,
                right=right,
                line=expr.line,
                column=expr.column,
            )
        
        return expr
    
    def parse_and(self) -> Optional[ASTNode]:
        """Parse logical AND."""
        expr = self.parse_equality()
        
        while self.match(TokenType.AND):
            operator = self.previous.value
            right = self.parse_equality()
            expr = BinaryOp(
                left=expr,
                operator=operator,
                right=right,
                line=expr.line,
                column=expr.column,
            )
        
        return expr
    
    def parse_equality(self) -> Optional[ASTNode]:
        """Parse equality comparison."""
        expr = self.parse_comparison()
        
        while self.match(TokenType.EQUALS, TokenType.NOT_EQUALS):
            operator = self.previous.value
            right = self.parse_comparison()
            expr = BinaryOp(
                left=expr,
                operator=operator,
                right=right,
                line=expr.line,
                column=expr.column,
            )
        
        return expr
    
    def parse_comparison(self) -> Optional[ASTNode]:
        """Parse comparison operators."""
        expr = self.parse_term()
        
        while self.match(
            TokenType.LESS_THAN, TokenType.GREATER_THAN,
            TokenType.LESS_EQUAL, TokenType.GREATER_EQUAL
        ):
            operator = self.previous.value
            right = self.parse_term()
            expr = BinaryOp(
                left=expr,
                operator=operator,
                right=right,
                line=expr.line,
                column=expr.column,
            )
        
        return expr
    
    def parse_term(self) -> Optional[ASTNode]:
        """Parse addition/subtraction."""
        expr = self.parse_factor()
        
        while self.match(TokenType.PLUS, TokenType.MINUS):
            operator = self.previous.value
            right = self.parse_factor()
            expr = BinaryOp(
                left=expr,
                operator=operator,
                right=right,
                line=expr.line,
                column=expr.column,
            )
        
        return expr
    
    def parse_factor(self) -> Optional[ASTNode]:
        """Parse multiplication/division."""
        expr = self.parse_unary()
        
        while self.match(TokenType.MULTIPLY, TokenType.DIVIDE, TokenType.MODULO):
            operator = self.previous.value
            right = self.parse_unary()
            expr = BinaryOp(
                left=expr,
                operator=operator,
                right=right,
                line=expr.line,
                column=expr.column,
            )
        
        return expr
    
    def parse_unary(self) -> Optional[ASTNode]:
        """Parse unary operators."""
        if self.match(TokenType.MINUS, TokenType.NOT):
            operator = self.previous.value
            operand = self.parse_unary()
            return UnaryOp(
                operator=operator,
                operand=operand,
                line=self.previous.line,
                column=self.previous.column,
            )
        
        return self.parse_call()
    
    def parse_call(self) -> Optional[ASTNode]:
        """Parse function calls and index access."""
        expr = self.parse_primary()
        
        while True:
            if self.match(TokenType.LPAREN):
                # Function call
                arguments = []
                if not self.check(TokenType.RPAREN):
                    arguments.append(self.parse_expression())
                    while self.match(TokenType.COMMA):
                        arguments.append(self.parse_expression())
                
                self.expect(TokenType.RPAREN, "Expected ')' after arguments")
                
                if isinstance(expr, Identifier):
                    expr = FunctionCall(
                        name=expr.name,
                        arguments=arguments,
                        line=expr.line,
                        column=expr.column,
                    )
                    
            elif self.match(TokenType.LBRACKET):
                # Index access
                index = self.parse_expression()
                self.expect(TokenType.RBRACKET, "Expected ']'")
                expr = IndexAccess(
                    object=expr,
                    index=index,
                    line=expr.line,
                    column=expr.column,
                )
            else:
                break
        
        return expr
    
    def parse_primary(self) -> Optional[ASTNode]:
        """Parse primary expressions (literals, identifiers, etc.)."""
        # Number
        if self.match(TokenType.NUMBER):
            value = float(self.previous.value)
            if value.is_integer():
                value = int(value)
            return NumberLiteral(
                value=value,
                line=self.previous.line,
                column=self.previous.column,
            )
        
        # String
        if self.match(TokenType.STRING):
            return StringLiteral(
                value=self.previous.value,
                line=self.previous.line,
                column=self.previous.column,
            )
        
        # Boolean
        if self.match(TokenType.BOOLEAN, TokenType.TRUE, TokenType.FALSE):
            value = self.previous.value.lower() == 'true'
            return BooleanLiteral(
                value=value,
                line=self.previous.line,
                column=self.previous.column,
            )
        
        # Null
        if self.match(TokenType.NULL):
            return NullLiteral(
                line=self.previous.line,
                column=self.previous.column,
            )
        
        # Identifier
        if self.match(TokenType.IDENTIFIER):
            return Identifier(
                name=self.previous.value,
                line=self.previous.line,
                column=self.previous.column,
            )
        
        # Array literal
        if self.match(TokenType.LBRACKET):
            elements = []
            if not self.check(TokenType.RBRACKET):
                elements.append(self.parse_expression())
                while self.match(TokenType.COMMA):
                    elements.append(self.parse_expression())
            
            self.expect(TokenType.RBRACKET, "Expected ']'")
            return ArrayLiteral(
                elements=elements,
                line=self.previous.line,
                column=self.previous.column,
            )
        
        # Parenthesized expression
        if self.match(TokenType.LPAREN):
            expr = self.parse_expression()
            self.expect(TokenType.RPAREN, "Expected ')'")
            return expr
        
        # Unknown token
        if self.current:
            self.advance()  # Skip unknown token
        
        return None
