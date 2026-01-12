"""
Tests for ClearScript Lexer
"""

import pytest
from src.clearscript.lexer import Lexer, TokenType


def test_basic_tokens():
    """Test basic token recognition."""
    source = "int x = 5;"
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    
    assert tokens[0].type == TokenType.INT
    assert tokens[1].type == TokenType.IDENTIFIER
    assert tokens[2].type == TokenType.ASSIGN
    assert tokens[3].type == TokenType.NUMBER
    assert tokens[4].type == TokenType.SEMICOLON


def test_keywords():
    """Test keyword recognition."""
    source = "function goto label wait kill"
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    
    assert tokens[0].type == TokenType.FUNCTION
    assert tokens[1].type == TokenType.GOTO
    assert tokens[2].type == TokenType.LABEL
    assert tokens[3].type == TokenType.WAIT
    assert tokens[4].type == TokenType.KILL


def test_operators():
    """Test operator recognition."""
    source = "+ - * / == != < > <= >= && ||"
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    
    assert tokens[0].type == TokenType.PLUS
    assert tokens[1].type == TokenType.MINUS
    assert tokens[2].type == TokenType.MULTIPLY
    assert tokens[3].type == TokenType.DIVIDE
    assert tokens[4].type == TokenType.EQ
    assert tokens[5].type == TokenType.NEQ
    assert tokens[6].type == TokenType.LT
    assert tokens[7].type == TokenType.GT
    assert tokens[8].type == TokenType.LTE
    assert tokens[9].type == TokenType.GTE
    assert tokens[10].type == TokenType.AND
    assert tokens[11].type == TokenType.OR


def test_strings():
    """Test string literal recognition."""
    source = '"hello world"'
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    
    assert tokens[0].type == TokenType.STRING
    assert tokens[0].value == "hello world"


def test_numbers():
    """Test number recognition."""
    source = "42 3.14"
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    
    assert tokens[0].type == TokenType.NUMBER
    assert tokens[0].value == 42
    assert tokens[1].type == TokenType.NUMBER
    assert tokens[1].value == 3.14


def test_comments():
    """Test comment recognition."""
    source = """
    // Single line comment
    int x = 5; /* block comment */
    """
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    
    # Should have comment tokens
    comment_tokens = [t for t in tokens if t.type == TokenType.COMMENT]
    assert len(comment_tokens) == 2
