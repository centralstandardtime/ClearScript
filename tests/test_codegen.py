"""
Tests for ClearScript Code Generator
"""

import pytest
from src.clearscript.lexer import Lexer
from src.clearscript.parser import Parser
from src.clearscript.codegen import CodeGenerator


def compile_source(source):
    """Helper to compile source to StateScript."""
    lexer = Lexer(source)
    parser = Parser(lexer.tokenize())
    ast = parser.parse()
    codegen = CodeGenerator(ast)
    return codegen.generate()


def test_variable_init():
    """Test top-level variable generates INIT."""
    source = "int x = 5;"
    output = compile_source(source)
    
    assert "INIT x 5" in output


def test_function_generation():
    """Test function generates label and return."""
    source = """
    function test() {
        int x = 5;
    }
    """
    output = compile_source(source)
    
    assert ":test" in output
    assert "RETURN" in output


def test_function_call():
    """Test function call generates CALL."""
    source = """
    function test() {
        int x = 5;
    }
    test();
    """
    output = compile_source(source)
    
    assert "CALL test" in output


def test_if_statement():
    """Test if statement generates CALLIF pattern."""
    source = """
    int x = 5;
    if (x > 3) {
        x = 0;
    }
    """
    output = compile_source(source)
    
    assert "CALLIF" in output
    assert "GOTO" in output


def test_while_loop():
    """Test while loop generates loop labels."""
    source = """
    int x = 0;
    while (x < 10) {
        x++;
    }
    """
    output = compile_source(source)
    
    assert "_while_" in output
    assert "GOTO" in output
    assert "INC x" in output


def test_expressions_wrapped():
    """Test expressions are wrapped in {}."""
    source = "int x = 5 + 3;"
    output = compile_source(source)
    
    assert "{5 + 3}" in output


def test_strings_wrapped():
    """Test strings are wrapped in []."""
    source = """
    function test(name) {
        int x = 1;
    }
    test("hello");
    """
    output = compile_source(source)
    
    assert "[hello]" in output


def test_goto_statement():
    """Test goto generates GOTO command."""
    source = """
    label: myLabel
    goto myLabel;
    """
    output = compile_source(source)
    
    assert ":myLabel" in output
    assert "GOTO myLabel" in output


def test_increment():
    """Test increment generates INC."""
    source = """
    int x = 0;
    x++;
    """
    output = compile_source(source)
    
    assert "INC x" in output


def test_complete_example():
    """Test complete example compiles correctly."""
    source = """
    int count = 0;
    
    function increment() {
        count++;
    }
    
    label: start
        increment();
        if (count < 5) {
            goto start;
        }
        kill();
    """
    output = compile_source(source)
    
    assert "INIT count 0" in output
    assert ":increment" in output
    assert "INC count" in output
    assert ":start" in output
    assert "CALL increment" in output
    assert "KILL" in output
