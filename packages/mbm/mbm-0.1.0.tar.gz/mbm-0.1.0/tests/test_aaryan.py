"""
Tests for the Aaryan language interpreter.
"""

import pytest

from mbm.aaryan import AaryanInterpreter, Lexer, Parser, TokenType


class TestLexer:
    """Tests for the Aaryan lexer."""
    
    def test_tokenize_numbers(self):
        lexer = Lexer("42 3.14")
        tokens = lexer.tokenize()
        
        assert tokens[0].type == TokenType.NUMBER
        assert tokens[0].value == "42"
        assert tokens[1].type == TokenType.NUMBER
        assert tokens[1].value == "3.14"
    
    def test_tokenize_strings(self):
        lexer = Lexer('"hello" \'world\'')
        tokens = lexer.tokenize()
        
        assert tokens[0].type == TokenType.STRING
        assert tokens[0].value == "hello"
        assert tokens[1].type == TokenType.STRING
        assert tokens[1].value == "world"
    
    def test_tokenize_keywords(self):
        lexer = Lexer("let const fn if else while return")
        tokens = lexer.tokenize()
        
        expected = [
            TokenType.LET, TokenType.CONST, TokenType.FN,
            TokenType.IF, TokenType.ELSE, TokenType.WHILE, TokenType.RETURN
        ]
        
        for i, expected_type in enumerate(expected):
            assert tokens[i].type == expected_type
    
    def test_tokenize_operators(self):
        lexer = Lexer("+ - * / = == != < > <= >=")
        tokens = lexer.tokenize()
        
        expected = [
            TokenType.PLUS, TokenType.MINUS, TokenType.MULTIPLY,
            TokenType.DIVIDE, TokenType.ASSIGN, TokenType.EQUALS,
            TokenType.NOT_EQUALS, TokenType.LESS_THAN, TokenType.GREATER_THAN,
            TokenType.LESS_EQUAL, TokenType.GREATER_EQUAL
        ]
        
        for i, expected_type in enumerate(expected):
            assert tokens[i].type == expected_type
    
    def test_skip_comments(self):
        lexer = Lexer("42 # this is a comment\n43")
        tokens = lexer.tokenize()
        
        numbers = [t for t in tokens if t.type == TokenType.NUMBER]
        assert len(numbers) == 2
        assert numbers[0].value == "42"
        assert numbers[1].value == "43"


class TestParser:
    """Tests for the Aaryan parser."""
    
    def test_parse_number(self):
        lexer = Lexer("42")
        parser = Parser(lexer.tokenize())
        program = parser.parse()
        
        assert len(program.statements) == 1
    
    def test_parse_variable_declaration(self):
        lexer = Lexer("let x = 42")
        parser = Parser(lexer.tokenize())
        program = parser.parse()
        
        assert len(program.statements) == 1
        assert program.statements[0].name == "x"
    
    def test_parse_function_declaration(self):
        lexer = Lexer("fn greet(name) { print name }")
        parser = Parser(lexer.tokenize())
        program = parser.parse()
        
        assert len(program.statements) == 1
        assert program.statements[0].name == "greet"
        assert program.statements[0].parameters == ["name"]
    
    def test_parse_if_statement(self):
        lexer = Lexer("if x > 0 { print x }")
        parser = Parser(lexer.tokenize())
        program = parser.parse()
        
        assert len(program.statements) == 1
        assert parser.errors == []


class TestInterpreter:
    """Tests for the Aaryan interpreter."""
    
    def test_arithmetic(self):
        interpreter = AaryanInterpreter()
        
        assert interpreter.execute("2 + 3") == 5
        assert interpreter.execute("10 - 4") == 6
        assert interpreter.execute("3 * 4") == 12
        assert interpreter.execute("15 / 3") == 5
        assert interpreter.execute("10 % 3") == 1
    
    def test_comparison(self):
        interpreter = AaryanInterpreter()
        
        assert interpreter.execute("5 > 3") == True
        assert interpreter.execute("3 < 5") == True
        assert interpreter.execute("5 == 5") == True
        assert interpreter.execute("5 != 3") == True
        assert interpreter.execute("5 >= 5") == True
        assert interpreter.execute("3 <= 5") == True
    
    def test_string_concatenation(self):
        interpreter = AaryanInterpreter()
        
        result = interpreter.execute('"hello" + " " + "world"')
        assert result == "hello world"
    
    def test_variables(self):
        interpreter = AaryanInterpreter()
        
        interpreter.execute("let x = 42")
        assert interpreter.execute("x") == 42
        
        interpreter.execute("x = 100")
        assert interpreter.execute("x") == 100
    
    def test_array(self):
        interpreter = AaryanInterpreter()
        
        result = interpreter.execute("[1, 2, 3]")
        assert result == [1, 2, 3]
        
        interpreter.execute("let arr = [10, 20, 30]")
        assert interpreter.execute("arr[0]") == 10
        assert interpreter.execute("arr[2]") == 30
    
    def test_function(self):
        interpreter = AaryanInterpreter()
        
        code = """
fn add(a, b) {
    return a + b
}
add(3, 4)
"""
        result = interpreter.execute(code)
        assert result == 7
    
    def test_if_statement(self):
        interpreter = AaryanInterpreter()
        
        code = """
let x = 10
if x > 5 {
    x = 100
}
x
"""
        result = interpreter.execute(code)
        assert result == 100
    
    def test_while_loop(self):
        interpreter = AaryanInterpreter()
        
        code = """
let sum = 0
let i = 1
while i <= 5 {
    sum = sum + i
    i = i + 1
}
sum
"""
        result = interpreter.execute(code)
        assert result == 15
    
    def test_builtin_len(self):
        interpreter = AaryanInterpreter()
        
        assert interpreter.execute('len("hello")') == 5
        assert interpreter.execute('len([1, 2, 3])') == 3
    
    def test_builtin_range(self):
        interpreter = AaryanInterpreter()
        
        result = interpreter.execute('range(5)')
        assert result == [0, 1, 2, 3, 4]
        
        result = interpreter.execute('range(1, 4)')
        assert result == [1, 2, 3]


class TestSyntaxCheck:
    """Tests for syntax checking."""
    
    def test_valid_syntax(self):
        interpreter = AaryanInterpreter()
        errors = interpreter.check_syntax("let x = 42")
        assert errors == []
    
    def test_invalid_syntax(self):
        interpreter = AaryanInterpreter()
        errors = interpreter.check_syntax("let = 42")  # Missing variable name
        assert len(errors) > 0
