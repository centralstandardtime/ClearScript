"""
AST Node Definitions for ClearScript

This module defines all the Abstract Syntax Tree node types used
during parsing and code generation.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Any


@dataclass
class ASTNode:
    """Base class for all AST nodes."""
    line: int = 0
    column: int = 0


@dataclass
class Program(ASTNode):
    """Root node representing the entire program."""
    statements: List[ASTNode] = field(default_factory=list)


@dataclass
class VariableDeclaration(ASTNode):
    """Variable declaration: int x = 5;"""
    var_type: str = ""  # 'int', 'float', etc.
    name: str = ""
    value: Optional[ASTNode] = None


@dataclass
class Assignment(ASTNode):
    """Assignment statement: x = 5;"""
    target: str = ""
    value: Optional[ASTNode] = None


@dataclass
class ArrayAccess(ASTNode):
    """Array access: arr[index]"""
    name: str = ""
    index: Optional[ASTNode] = None


@dataclass
class ArrayAssignment(ASTNode):
    """Array assignment: portout[1] = 0;"""
    name: str = ""
    index: Optional[ASTNode] = None
    value: Optional[ASTNode] = None


@dataclass
class BinaryOp(ASTNode):
    """Binary operation: a + b, a && b, etc."""
    left: Optional[ASTNode] = None
    operator: str = ""  # '+', '-', '*', '/', '&&', '||', '==', '!=', '<', '>', '<=', '>='
    right: Optional[ASTNode] = None


@dataclass
class UnaryOp(ASTNode):
    """Unary operation: !x, -x, x++, x--"""
    operator: str = ""  # '!', '-', '++', '--'
    operand: Optional[ASTNode] = None
    is_postfix: bool = False  # For ++ and --


@dataclass
class Literal(ASTNode):
    """Literal value: 42, 3.14, "hello" """
    value: Any = None
    literal_type: str = ""  # 'int', 'float', 'string'


@dataclass
class Identifier(ASTNode):
    """Variable or function identifier."""
    name: str = ""


@dataclass
class CallbackDeclaration(ASTNode):
    """Callback declaration: callback portin[1] up { ... }"""
    port_type: str = ""  # 'portin', 'portout'
    port_number: Optional[ASTNode] = None
    trigger: str = ""  # 'up', 'down', etc.
    body: List[ASTNode] = field(default_factory=list)


@dataclass
class IfStatement(ASTNode):
    """If/else statement."""
    condition: Optional[ASTNode] = None
    then_body: List[ASTNode] = field(default_factory=list)
    else_body: Optional[List[ASTNode]] = None


@dataclass
class WhileStatement(ASTNode):
    """While loop."""
    condition: Optional[ASTNode] = None
    body: List[ASTNode] = field(default_factory=list)


@dataclass
class DoInBlock(ASTNode):
    """Do-in block for scheduled execution: do in 500 { ... }"""
    delay: Optional[ASTNode] = None  # milliseconds
    body: List[ASTNode] = field(default_factory=list)


@dataclass
class ExpressionStatement(ASTNode):
    """Statement that wraps an expression."""
    expression: Optional[ASTNode] = None


@dataclass
class Comment(ASTNode):
    """Comment (preserved for documentation)."""
    text: str = ""
    is_block: bool = False  # True for /* */, False for //


# === StateScript-Specific Nodes ===

@dataclass
class FunctionDeclaration(ASTNode):
    """Function declaration: function name(param1, param2) { ... }"""
    name: str = ""
    params: List[str] = field(default_factory=list)
    body: List[ASTNode] = field(default_factory=list)


@dataclass
class LabelDeclaration(ASTNode):
    """Label declaration: label: name"""
    name: str = ""


@dataclass
class GotoStatement(ASTNode):
    """Goto statement: goto label; or goto label if (condition);"""
    label: str = ""
    condition: Optional[ASTNode] = None


@dataclass
class WaitStatement(ASTNode):
    """Wait statement: wait(time);"""
    time: Optional[ASTNode] = None
    result_var: str = ""  # Optional variable to store actual wait time


@dataclass
class WaitForStatement(ASTNode):
    """WaitFor statement: waitfor(condition);"""
    condition: Optional[ASTNode] = None


@dataclass
class KillStatement(ASTNode):
    """Kill statement: kill();"""
    pass  # No fields needed


@dataclass
class ReturnStatement(ASTNode):
    """Return statement: return;"""
    pass  # No fields needed


@dataclass
class ThreadStatement(ASTNode):
    """Thread statement: thread(label, arg1, arg2, ...);"""
    label: str = ""
    args: List[ASTNode] = field(default_factory=list)


@dataclass
class SetStatement(ASTNode):
    """Set statement: set(var, value);"""
    variable: str = ""
    value: Optional[ASTNode] = None


@dataclass
class PushStatement(ASTNode):
    """Push statement: push(value);"""
    value: Optional[ASTNode] = None


@dataclass
class PopStatement(ASTNode):
    """Pop statement: pop(variable);"""
    variable: str = ""


@dataclass
class PeekStatement(ASTNode):
    """Peek statement: peek(variable);"""
    variable: str = ""


@dataclass
class SpawnBotCall(ASTNode):
    """SpawnBot call: spawnbot(template, location, attr1, val1, ...);"""
    template: Optional[ASTNode] = None
    location: Optional[ASTNode] = None
    attributes: List[ASTNode] = field(default_factory=list)  # Pairs of attr/value


@dataclass
class MoveToCall(ASTNode):
    """MoveTo call: moveto(prop, location);"""
    prop: Optional[ASTNode] = None
    location: Optional[ASTNode] = None


@dataclass
class AnimateCall(ASTNode):
    """Animate call: animate(prop, location, time);"""
    prop: Optional[ASTNode] = None
    location: Optional[ASTNode] = None
    time: Optional[ASTNode] = None


@dataclass
class DeleteCall(ASTNode):
    """Delete call: delete(prop);"""
    prop: Optional[ASTNode] = None


@dataclass
class FunctionCall(ASTNode):
    """User-defined function call: functionName(arg1, arg2, ...);"""
    name: str = ""
    args: List[ASTNode] = field(default_factory=list)


@dataclass
class RawBlock(ASTNode):
    """Raw StateScript block: raw { ... }"""
    code: str = ""


# ============================================================================
# OOP and Advanced Features
# ============================================================================

@dataclass
class ClassDeclaration(ASTNode):
    """Class declaration: class Name { properties... methods... }"""
    name: str = ""
    properties: List[ASTNode] = field(default_factory=list)  # VariableDeclaration nodes
    methods: List[ASTNode] = field(default_factory=list)  # MethodDeclaration nodes


@dataclass
class StructDeclaration(ASTNode):
    """Struct declaration: struct Name { properties... }"""
    name: str = ""
    properties: List[ASTNode] = field(default_factory=list)


@dataclass
class MethodDeclaration(ASTNode):
    """Method declaration: method name(params) { body }"""
    name: str = ""
    params: List[str] = field(default_factory=list)
    body: List[ASTNode] = field(default_factory=list)


@dataclass
class MemberAccess(ASTNode):
    """Member access: object.property"""
    object: Optional[ASTNode] = None  # Identifier or nested MemberAccess
    member: str = ""


@dataclass
class ArrayDeclaration(ASTNode):
    """Array declaration: int[] arr = [1, 2, 3]"""
    elem_type: str = ""  # int, float, etc.
    name: str = ""
    size: Optional[ASTNode] = None  # Optional size expression
    initializer: Optional[ASTNode] = None  # ArrayLiteral or None


@dataclass
class ArrayLiteral(ASTNode):
    """Array literal: [1, 2, 3]"""
    elements: List[ASTNode] = field(default_factory=list)


@dataclass
class ArrayAccess(ASTNode):
    """Array access: arr[index]"""
    array: Optional[ASTNode] = None  # Identifier or nested expression
    index: Optional[ASTNode] = None


@dataclass
class ForLoop(ASTNode):
    """For loop: for (init; condition; increment) { body }"""
    init: Optional[ASTNode] = None
    condition: Optional[ASTNode] = None
    increment: Optional[ASTNode] = None
    body: List[ASTNode] = field(default_factory=list)


@dataclass
class ForEachLoop(ASTNode):
    """Foreach loop: for (item in array) { body }"""
    var_type: str = ""
    var_name: str = ""
    iterable: Optional[ASTNode] = None
    body: List[ASTNode] = field(default_factory=list)


@dataclass
class SwitchStatement(ASTNode):
    """Switch statement: switch (expr) { case...: ... }"""
    expression: Optional[ASTNode] = None
    cases: List[ASTNode] = field(default_factory=list)  # CaseStatement nodes
    default_case: Optional[ASTNode] = None  # DefaultCase node


@dataclass
class CaseStatement(ASTNode):
    """Case statement: case value: statements..."""
    value: Optional[ASTNode] = None
    statements: List[ASTNode] = field(default_factory=list)


@dataclass
class DefaultCase(ASTNode):
    """Default case: default: statements..."""
    statements: List[ASTNode] = field(default_factory=list)


@dataclass
class BreakStatement(ASTNode):
    """Break statement: break;"""
    pass


@dataclass
class TernaryExpression(ASTNode):
    """Ternary expression: condition ? true_val : false_val"""
    condition: Optional[ASTNode] = None
    true_value: Optional[ASTNode] = None
    false_value: Optional[ASTNode] = None


@dataclass
class ConstDeclaration(ASTNode):
    """Const declaration: const int MAX = 100;"""
    var_type: str = ""
    name: str = ""
    value: Optional[ASTNode] = None


@dataclass
class EnumDeclaration(ASTNode):
    """Enum declaration: enum Name { A, B, C }"""
    name: str = ""
    values: List[str] = field(default_factory=list)
