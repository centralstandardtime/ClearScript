"""
ClearScript - A C-styled, highly readable language that compiles to StateScript.

Version: 0.1.0
"""

__version__ = "0.1.0"
__author__ = "ClearScript Contributors"

from .lexer import Lexer
from .parser import Parser
from .codegen import CodeGenerator

__all__ = ["Lexer", "Parser", "CodeGenerator", "__version__"]
