"""
Tests for ClearScript Parser
"""

import pytest
from src.clearscript.lexer import Lexer
from src.clearscript.parser import Parser
from src.clearscript.ast_nodes import *


def test_variable_declaration():
    """Test parsing variable declarations."""
    source = "int x = 5;"
    lexer = Lexer(source)
    parser = Parser(lexer.tokenize())
    program = parser.parse()
    
    assert len(program.statements) == 1
    assert isinstance(program.statements[0], VariableDeclaration)
    assert program.statements[0].var_type == "int"
    assert program.statements[0].name == "x"


def test_function_declaration():
    """Test parsing function declarations."""
    source = """
    function add(a, b) {
        int result = a + b;
    }
    """
    lexer = Lexer(source)
    parser = Parser(lexer.tokenize())
    program = parser.parse()
    
    assert len(program.statements) == 1
    assert isinstance(program.statements[0], FunctionDeclaration)
    assert program.statements[0].name == "add"
    assert len(program.statements[0].params) == 2
    assert program.statements[0].params[0] == "a"
    assert program.statements[0].params[1] == "b"


def test_if_statement():
    """Test parsing if statements."""
    source = """
    if (x > 5) {
        x = 0;
    }
    """
    lexer = Lexer(source)
    parser = Parser(lexer.tokenize())
    program = parser.parse()
    
    assert len(program.statements) == 1
    assert isinstance(program.statements[0], IfStatement)
    assert program.statements[0].condition is not None


def test_while_statement():
    """Test parsing while statements."""
    source = """
    while (x < 10) {
        x++;
    }
    """
    lexer = Lexer(source)
    parser = Parser(lexer.tokenize())
    program = parser.parse()
    
    assert len(program.statements) == 1
    assert isinstance(program.statements[0], WhileStatement)


def test_function_call():
    """Test parsing function calls."""
    source = "myFunction(arg1, arg2);"
    lexer = Lexer(source)
    parser = Parser(lexer.tokenize())
    program = parser.parse()
    
    assert len(program.statements) == 1
    expr_stmt = program.statements[0]
    assert isinstance(expr_stmt, ExpressionStatement)
    assert isinstance(expr_stmt.expression, FunctionCall)
    assert expr_stmt.expression.name == "myFunction"
    assert len(expr_stmt.expression.args) == 2


def test_goto_statement():
    """Test parsing goto statements."""
    source = "goto myLabel;"
    lexer = Lexer(source)
    parser = Parser(lexer.tokenize())
    program = parser.parse()
    
    assert len(program.statements) == 1
    assert isinstance(program.statements[0], GotoStatement)
    assert program.statements[0].label == "myLabel"


def test_label_declaration():
    """Test parsing label declarations."""
    source = "label: myLabel"
    lexer = Lexer(source)
    parser = Parser(lexer.tokenize())
    program = parser.parse()
    
    assert len(program.statements) == 1
    assert isinstance(program.statements[0], LabelDeclaration)
    assert program.statements[0].name == "myLabel"
