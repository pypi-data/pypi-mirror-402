"""
Aaryan Language AST

Abstract Syntax Tree node definitions for the Aaryan language.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional


class ASTNode(ABC):
    """Base class for all AST nodes."""
    
    line: int = 0
    column: int = 0
    
    @abstractmethod
    def accept(self, visitor: ASTVisitor) -> Any:
        """Accept a visitor for traversal."""
        pass


class ASTVisitor(ABC):
    """Base visitor class for AST traversal."""
    
    @abstractmethod
    def visit(self, node: ASTNode) -> Any:
        """Visit an AST node."""
        pass


# =============================================================================
# Expression Nodes
# =============================================================================

@dataclass
class NumberLiteral(ASTNode):
    """Numeric literal (int or float)."""
    value: float
    line: int = 0
    column: int = 0
    
    def accept(self, visitor: ASTVisitor) -> Any:
        return visitor.visit(self)


@dataclass
class StringLiteral(ASTNode):
    """String literal."""
    value: str
    line: int = 0
    column: int = 0
    
    def accept(self, visitor: ASTVisitor) -> Any:
        return visitor.visit(self)


@dataclass
class BooleanLiteral(ASTNode):
    """Boolean literal (true/false)."""
    value: bool
    line: int = 0
    column: int = 0
    
    def accept(self, visitor: ASTVisitor) -> Any:
        return visitor.visit(self)


@dataclass
class NullLiteral(ASTNode):
    """Null literal."""
    line: int = 0
    column: int = 0
    
    def accept(self, visitor: ASTVisitor) -> Any:
        return visitor.visit(self)


@dataclass
class Identifier(ASTNode):
    """Variable or function identifier."""
    name: str
    line: int = 0
    column: int = 0
    
    def accept(self, visitor: ASTVisitor) -> Any:
        return visitor.visit(self)


@dataclass
class BinaryOp(ASTNode):
    """Binary operation (a + b, a == b, etc.)."""
    left: ASTNode
    operator: str
    right: ASTNode
    line: int = 0
    column: int = 0
    
    def accept(self, visitor: ASTVisitor) -> Any:
        return visitor.visit(self)


@dataclass
class UnaryOp(ASTNode):
    """Unary operation (-a, not a)."""
    operator: str
    operand: ASTNode
    line: int = 0
    column: int = 0
    
    def accept(self, visitor: ASTVisitor) -> Any:
        return visitor.visit(self)


@dataclass
class FunctionCall(ASTNode):
    """Function call."""
    name: str
    arguments: list[ASTNode] = field(default_factory=list)
    line: int = 0
    column: int = 0
    
    def accept(self, visitor: ASTVisitor) -> Any:
        return visitor.visit(self)


@dataclass
class ArrayLiteral(ASTNode):
    """Array literal [1, 2, 3]."""
    elements: list[ASTNode] = field(default_factory=list)
    line: int = 0
    column: int = 0
    
    def accept(self, visitor: ASTVisitor) -> Any:
        return visitor.visit(self)


@dataclass
class IndexAccess(ASTNode):
    """Array/string index access: arr[0]."""
    object: ASTNode
    index: ASTNode
    line: int = 0
    column: int = 0
    
    def accept(self, visitor: ASTVisitor) -> Any:
        return visitor.visit(self)


# =============================================================================
# Statement Nodes
# =============================================================================

@dataclass
class Program(ASTNode):
    """Root node containing all statements."""
    statements: list[ASTNode] = field(default_factory=list)
    line: int = 0
    column: int = 0
    
    def accept(self, visitor: ASTVisitor) -> Any:
        return visitor.visit(self)


@dataclass
class ExpressionStatement(ASTNode):
    """Expression as a statement."""
    expression: ASTNode
    line: int = 0
    column: int = 0
    
    def accept(self, visitor: ASTVisitor) -> Any:
        return visitor.visit(self)


@dataclass
class VariableDeclaration(ASTNode):
    """Variable declaration (let x = 5)."""
    name: str
    value: Optional[ASTNode] = None
    is_const: bool = False
    line: int = 0
    column: int = 0
    
    def accept(self, visitor: ASTVisitor) -> Any:
        return visitor.visit(self)


@dataclass
class Assignment(ASTNode):
    """Variable assignment (x = 5)."""
    name: str
    value: ASTNode
    line: int = 0
    column: int = 0
    
    def accept(self, visitor: ASTVisitor) -> Any:
        return visitor.visit(self)


@dataclass
class PrintStatement(ASTNode):
    """Print statement."""
    expression: ASTNode
    line: int = 0
    column: int = 0
    
    def accept(self, visitor: ASTVisitor) -> Any:
        return visitor.visit(self)


@dataclass
class Block(ASTNode):
    """Block of statements { ... }."""
    statements: list[ASTNode] = field(default_factory=list)
    line: int = 0
    column: int = 0
    
    def accept(self, visitor: ASTVisitor) -> Any:
        return visitor.visit(self)


@dataclass
class IfStatement(ASTNode):
    """If/else statement."""
    condition: ASTNode
    then_branch: ASTNode
    else_branch: Optional[ASTNode] = None
    line: int = 0
    column: int = 0
    
    def accept(self, visitor: ASTVisitor) -> Any:
        return visitor.visit(self)


@dataclass
class WhileStatement(ASTNode):
    """While loop."""
    condition: ASTNode
    body: ASTNode
    line: int = 0
    column: int = 0
    
    def accept(self, visitor: ASTVisitor) -> Any:
        return visitor.visit(self)


@dataclass
class ForStatement(ASTNode):
    """For loop."""
    variable: str
    iterable: ASTNode
    body: ASTNode
    line: int = 0
    column: int = 0
    
    def accept(self, visitor: ASTVisitor) -> Any:
        return visitor.visit(self)


@dataclass
class FunctionDeclaration(ASTNode):
    """Function declaration."""
    name: str
    parameters: list[str] = field(default_factory=list)
    body: ASTNode = None
    line: int = 0
    column: int = 0
    
    def accept(self, visitor: ASTVisitor) -> Any:
        return visitor.visit(self)


@dataclass
class ReturnStatement(ASTNode):
    """Return statement."""
    value: Optional[ASTNode] = None
    line: int = 0
    column: int = 0
    
    def accept(self, visitor: ASTVisitor) -> Any:
        return visitor.visit(self)
