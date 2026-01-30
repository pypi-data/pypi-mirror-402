"""
Aaryan Language Interpreter

Executes Aaryan programs by walking the AST.
"""

from __future__ import annotations

from typing import Any, Optional, Callable

from mbm.aaryan.lexer import Lexer
from mbm.aaryan.parser import Parser
from mbm.aaryan.ast import (
    ASTNode, ASTVisitor, Program, NumberLiteral, StringLiteral,
    BooleanLiteral, NullLiteral, Identifier, BinaryOp, UnaryOp,
    FunctionCall, ArrayLiteral, IndexAccess, ExpressionStatement,
    VariableDeclaration, Assignment, PrintStatement, Block,
    IfStatement, WhileStatement, ForStatement, FunctionDeclaration,
    ReturnStatement,
)
from mbm.core.exceptions import RuntimeError as AaryanRuntimeError


class ReturnValue(Exception):
    """Exception used to implement return statements."""
    
    def __init__(self, value: Any):
        self.value = value


class Environment:
    """
    Variable environment with scope support.
    """
    
    def __init__(self, parent: Optional[Environment] = None):
        self.variables: dict[str, Any] = {}
        self.constants: set[str] = set()
        self.parent = parent
    
    def define(self, name: str, value: Any, is_const: bool = False) -> None:
        """Define a new variable."""
        self.variables[name] = value
        if is_const:
            self.constants.add(name)
    
    def get(self, name: str) -> Any:
        """Get a variable's value."""
        if name in self.variables:
            return self.variables[name]
        if self.parent:
            return self.parent.get(name)
        raise AaryanRuntimeError(f"Undefined variable: {name}")
    
    def set(self, name: str, value: Any) -> None:
        """Set a variable's value."""
        if name in self.constants:
            raise AaryanRuntimeError(f"Cannot reassign constant: {name}")
        
        if name in self.variables:
            self.variables[name] = value
        elif self.parent:
            self.parent.set(name, value)
        else:
            raise AaryanRuntimeError(f"Undefined variable: {name}")
    
    def exists(self, name: str) -> bool:
        """Check if a variable exists."""
        if name in self.variables:
            return True
        if self.parent:
            return self.parent.exists(name)
        return False


class AaryanFunction:
    """Represents a user-defined function."""
    
    def __init__(self, declaration: FunctionDeclaration, closure: Environment):
        self.declaration = declaration
        self.closure = closure
    
    def call(self, interpreter: AaryanInterpreter, arguments: list[Any]) -> Any:
        """Execute the function with given arguments."""
        # Create new environment for function scope
        env = Environment(self.closure)
        
        # Bind parameters to arguments
        for param, arg in zip(self.declaration.parameters, arguments):
            env.define(param, arg)
        
        # Execute function body
        try:
            interpreter.execute_block(self.declaration.body, env)
            return None
        except ReturnValue as ret:
            return ret.value


class AaryanInterpreter(ASTVisitor):
    """
    Interpreter for the Aaryan language.
    
    Executes Aaryan programs by walking the AST tree.
    """
    
    def __init__(self, trace: bool = False):
        """
        Initialize interpreter.
        
        Args:
            trace: Whether to print execution trace
        """
        self.trace = trace
        self.globals = Environment()
        self.environment = self.globals
        self.output: list[str] = []
        
        # Register built-in functions
        self._register_builtins()
    
    def _register_builtins(self) -> None:
        """Register built-in functions."""
        self.globals.define('len', self._builtin_len)
        self.globals.define('str', self._builtin_str)
        self.globals.define('int', self._builtin_int)
        self.globals.define('float', self._builtin_float)
        self.globals.define('type', self._builtin_type)
        self.globals.define('range', self._builtin_range)
        self.globals.define('input', self._builtin_input)
    
    def _builtin_len(self, args: list[Any]) -> int:
        """Built-in len function."""
        if len(args) != 1:
            raise AaryanRuntimeError("len() takes exactly 1 argument")
        arg = args[0]
        if isinstance(arg, (str, list)):
            return len(arg)
        raise AaryanRuntimeError("len() argument must be string or array")
    
    def _builtin_str(self, args: list[Any]) -> str:
        """Built-in str function."""
        if len(args) != 1:
            raise AaryanRuntimeError("str() takes exactly 1 argument")
        return self._stringify(args[0])
    
    def _builtin_int(self, args: list[Any]) -> int:
        """Built-in int function."""
        if len(args) != 1:
            raise AaryanRuntimeError("int() takes exactly 1 argument")
        try:
            return int(args[0])
        except (ValueError, TypeError):
            raise AaryanRuntimeError(f"Cannot convert to int: {args[0]}")
    
    def _builtin_float(self, args: list[Any]) -> float:
        """Built-in float function."""
        if len(args) != 1:
            raise AaryanRuntimeError("float() takes exactly 1 argument")
        try:
            return float(args[0])
        except (ValueError, TypeError):
            raise AaryanRuntimeError(f"Cannot convert to float: {args[0]}")
    
    def _builtin_type(self, args: list[Any]) -> str:
        """Built-in type function."""
        if len(args) != 1:
            raise AaryanRuntimeError("type() takes exactly 1 argument")
        arg = args[0]
        if arg is None:
            return "null"
        if isinstance(arg, bool):
            return "boolean"
        if isinstance(arg, int):
            return "int"
        if isinstance(arg, float):
            return "float"
        if isinstance(arg, str):
            return "string"
        if isinstance(arg, list):
            return "array"
        if callable(arg):
            return "function"
        return "unknown"
    
    def _builtin_range(self, args: list[Any]) -> list[int]:
        """Built-in range function."""
        if len(args) == 1:
            return list(range(int(args[0])))
        elif len(args) == 2:
            return list(range(int(args[0]), int(args[1])))
        elif len(args) == 3:
            return list(range(int(args[0]), int(args[1]), int(args[2])))
        raise AaryanRuntimeError("range() takes 1 to 3 arguments")
    
    def _builtin_input(self, args: list[Any]) -> str:
        """Built-in input function."""
        prompt = ""
        if args:
            prompt = self._stringify(args[0])
        return input(prompt)
    
    def execute(self, source: str) -> Any:
        """
        Execute Aaryan source code.
        
        Args:
            source: Source code string
            
        Returns:
            Result of execution
        """
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        
        parser = Parser(tokens)
        program = parser.parse()
        
        if parser.errors:
            raise AaryanRuntimeError(f"Parse errors: {parser.errors}")
        
        return self.visit(program)
    
    def execute_block(self, block: Block, environment: Environment) -> Any:
        """Execute a block in a given environment."""
        previous = self.environment
        try:
            self.environment = environment
            result = None
            for stmt in block.statements:
                result = self.visit(stmt)
            return result
        finally:
            self.environment = previous
    
    def check_syntax(self, source: str) -> list[str]:
        """
        Check source code for syntax errors.
        
        Args:
            source: Source code string
            
        Returns:
            List of error messages
        """
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        
        parser = Parser(tokens)
        parser.parse()
        
        return parser.errors
    
    def visit(self, node: ASTNode) -> Any:
        """Visit an AST node."""
        if node is None:
            return None
        
        method_name = f'visit_{type(node).__name__}'
        visitor = getattr(self, method_name, self.generic_visit)
        
        if self.trace:
            print(f"[TRACE] {method_name}")
        
        return visitor(node)
    
    def generic_visit(self, node: ASTNode) -> Any:
        """Default visitor for unknown nodes."""
        raise AaryanRuntimeError(f"No visitor for {type(node).__name__}")
    
    def visit_Program(self, node: Program) -> Any:
        result = None
        for stmt in node.statements:
            result = self.visit(stmt)
        return result
    
    def visit_NumberLiteral(self, node: NumberLiteral) -> float:
        return node.value
    
    def visit_StringLiteral(self, node: StringLiteral) -> str:
        return node.value
    
    def visit_BooleanLiteral(self, node: BooleanLiteral) -> bool:
        return node.value
    
    def visit_NullLiteral(self, node: NullLiteral) -> None:
        return None
    
    def visit_Identifier(self, node: Identifier) -> Any:
        return self.environment.get(node.name)
    
    def visit_BinaryOp(self, node: BinaryOp) -> Any:
        left = self.visit(node.left)
        right = self.visit(node.right)
        
        op = node.operator
        
        # Arithmetic
        if op == '+':
            if isinstance(left, str) or isinstance(right, str):
                return self._stringify(left) + self._stringify(right)
            return left + right
        if op == '-':
            return left - right
        if op == '*':
            return left * right
        if op == '/':
            if right == 0:
                raise AaryanRuntimeError("Division by zero", node.line)
            return left / right
        if op == '%':
            return left % right
        
        # Comparison
        if op == '==':
            return left == right
        if op == '!=':
            return left != right
        if op == '<':
            return left < right
        if op == '>':
            return left > right
        if op == '<=':
            return left <= right
        if op == '>=':
            return left >= right
        
        # Logical
        if op.lower() == 'and':
            return self._is_truthy(left) and self._is_truthy(right)
        if op.lower() == 'or':
            return self._is_truthy(left) or self._is_truthy(right)
        
        raise AaryanRuntimeError(f"Unknown operator: {op}", node.line)
    
    def visit_UnaryOp(self, node: UnaryOp) -> Any:
        operand = self.visit(node.operand)
        
        if node.operator == '-':
            return -operand
        if node.operator.lower() == 'not':
            return not self._is_truthy(operand)
        
        raise AaryanRuntimeError(f"Unknown unary operator: {node.operator}")
    
    def visit_FunctionCall(self, node: FunctionCall) -> Any:
        callee = self.environment.get(node.name)
        arguments = [self.visit(arg) for arg in node.arguments]
        
        # Built-in function
        if callable(callee) and not isinstance(callee, AaryanFunction):
            return callee(arguments)
        
        # User-defined function
        if isinstance(callee, AaryanFunction):
            if len(arguments) != len(callee.declaration.parameters):
                raise AaryanRuntimeError(
                    f"Expected {len(callee.declaration.parameters)} arguments, "
                    f"got {len(arguments)}",
                    node.line,
                )
            return callee.call(self, arguments)
        
        raise AaryanRuntimeError(f"'{node.name}' is not callable", node.line)
    
    def visit_ArrayLiteral(self, node: ArrayLiteral) -> list[Any]:
        return [self.visit(elem) for elem in node.elements]
    
    def visit_IndexAccess(self, node: IndexAccess) -> Any:
        obj = self.visit(node.object)
        index = self.visit(node.index)
        
        if isinstance(obj, (list, str)):
            try:
                return obj[int(index)]
            except IndexError:
                raise AaryanRuntimeError(f"Index out of bounds: {index}", node.line)
        
        raise AaryanRuntimeError("Can only index arrays and strings", node.line)
    
    def visit_ExpressionStatement(self, node: ExpressionStatement) -> Any:
        return self.visit(node.expression)
    
    def visit_VariableDeclaration(self, node: VariableDeclaration) -> None:
        value = None
        if node.value:
            value = self.visit(node.value)
        
        self.environment.define(node.name, value, node.is_const)
    
    def visit_Assignment(self, node: Assignment) -> Any:
        value = self.visit(node.value)
        self.environment.set(node.name, value)
        return value
    
    def visit_PrintStatement(self, node: PrintStatement) -> None:
        value = self.visit(node.expression)
        output = self._stringify(value)
        print(output)
        self.output.append(output)
    
    def visit_Block(self, node: Block) -> Any:
        env = Environment(self.environment)
        return self.execute_block(node, env)
    
    def visit_IfStatement(self, node: IfStatement) -> Any:
        if self._is_truthy(self.visit(node.condition)):
            return self.visit(node.then_branch)
        elif node.else_branch:
            return self.visit(node.else_branch)
        return None
    
    def visit_WhileStatement(self, node: WhileStatement) -> None:
        while self._is_truthy(self.visit(node.condition)):
            self.visit(node.body)
    
    def visit_ForStatement(self, node: ForStatement) -> None:
        iterable = self.visit(node.iterable)
        
        if not isinstance(iterable, (list, str, range)):
            raise AaryanRuntimeError("Can only iterate over arrays or strings", node.line)
        
        for item in iterable:
            env = Environment(self.environment)
            env.define(node.variable, item)
            self.execute_block(node.body, env)
    
    def visit_FunctionDeclaration(self, node: FunctionDeclaration) -> None:
        function = AaryanFunction(node, self.environment)
        self.environment.define(node.name, function)
    
    def visit_ReturnStatement(self, node: ReturnStatement) -> None:
        value = None
        if node.value:
            value = self.visit(node.value)
        raise ReturnValue(value)
    
    def _is_truthy(self, value: Any) -> bool:
        """Check if a value is truthy."""
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value != 0
        if isinstance(value, str):
            return len(value) > 0
        if isinstance(value, list):
            return len(value) > 0
        return True
    
    def _stringify(self, value: Any) -> str:
        """Convert a value to string."""
        if value is None:
            return "null"
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, float):
            if value.is_integer():
                return str(int(value))
        if isinstance(value, list):
            items = ", ".join(self._stringify(item) for item in value)
            return f"[{items}]"
        return str(value)
