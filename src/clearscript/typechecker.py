"""
Type Checker for ClearScript

Performs static type checking on the AST before code generation.
"""

from typing import Dict, List, Optional
from .ast_nodes import *


class TypeCheckError(Exception):
    """Type checking error"""
    def __init__(self, message: str, line: int = 0):
        self.message = message
        self.line = line
        super().__init__(f"Line {line}: {message}" if line else message)


class TypeChecker:
    """Type checker for ClearScript AST"""
    
    def __init__(self, ast: Program):
        self.ast = ast
        self.symbol_table: Dict[str, str] = {}  # name -> type
        self.errors: List[TypeCheckError] = []
        self.current_function = None
    
    def check(self) -> List[TypeCheckError]:
        """Run type checking and return list of errors"""
        try:
            self.visit(self.ast)
        except TypeCheckError as e:
            self.errors.append(e)
        
        return self.errors
    
    def visit(self, node: ASTNode):
        """Dispatch to appropriate visitor method"""
        if isinstance(node, Program):
            for stmt in node.statements:
                self.visit(stmt)
        
        elif isinstance(node, VariableDeclaration):
            self.visit_variable_declaration(node)
        
        elif isinstance(node, ArrayDeclaration):
            self.visit_array_declaration(node)
        
        elif isinstance(node, Assignment):
            self.visit_assignment(node)
        
        elif isinstance(node, IfStatement):
            self.visit_if_statement(node)
        
        elif isinstance(node, WhileStatement):
            self.visit_while_statement(node)
        
        elif isinstance(node, ForLoop):
            self.visit_for_loop(node)
        
        elif isinstance(node, FunctionDeclaration):
            self.visit_function_declaration(node)
        
        elif isinstance(node, ExpressionStatement):
            self.infer_type(node.expression)
        
        # Ignore other node types for now
    
    def visit_variable_declaration(self, node: VariableDeclaration):
        """Check variable declaration"""
        # Register variable type
        self.symbol_table[node.name] = node.var_type
        
        # Check initializer type if present
        if node.value:
            value_type = self.infer_type(node.value)
            if not self.types_compatible(node.var_type, value_type):
                raise TypeCheckError(
                    f"Cannot initialize variable '{node.name}' of type '{node.var_type}' with value of type '{value_type}'",
                    node.line
                )
    
    def visit_array_declaration(self, node: ArrayDeclaration):
        """Check array declaration"""
        array_type = f"{node.elem_type}[]"
        self.symbol_table[node.name] = array_type
        
        # Check array literal elements if present
        if node.initializer and isinstance(node.initializer, ArrayLiteral):
            for elem in node.initializer.elements:
                elem_type = self.infer_type(elem)
                if not self.types_compatible(node.elem_type, elem_type):
                    raise TypeCheckError(
                        f"Array element type '{elem_type}' does not match array type '{node.elem_type}[]'",
                        node.line
                    )
    
    def visit_assignment(self, node: Assignment):
        """Check assignment type compatibility"""
        if node.target not in self.symbol_table:
            raise TypeCheckError(
                f"Undefined variable '{node.target}'",
                node.line
            )
        
        target_type = self.symbol_table[node.target]
        value_type = self.infer_type(node.value)
        
        if not self.types_compatible(target_type, value_type):
            raise TypeCheckError(
                f"Cannot assign value of type '{value_type}' to variable '{node.target}' of type '{target_type}'",
                node.line
            )
    
    def visit_if_statement(self, node: IfStatement):
        """Check if statement"""
        # Condition should be boolean-like (we accept any type for now)
        self.infer_type(node.condition)
        
        for stmt in node.then_body:
            self.visit(stmt)
        
        if node.else_body:
            for stmt in node.else_body:
                self.visit(stmt)
    
    def visit_while_statement(self, node: WhileStatement):
        """Check while statement"""
        self.infer_type(node.condition)
        
        for stmt in node.body:
            self.visit(stmt)
    
    def visit_for_loop(self, node: ForLoop):
        """Check for loop"""
        if node.init:
            self.visit(node.init)
        if node.condition:
            self.infer_type(node.condition)
        if node.increment:
            self.infer_type(node.increment)
        
        for stmt in node.body:
            self.visit(stmt)
    
    def visit_function_declaration(self, node: FunctionDeclaration):
        """Check function declaration"""
        # Register function (simplified - no full signature tracking)
        self.current_function = node.name
        
        # Check function body
        for stmt in node.body:
            self.visit(stmt)
        
        self.current_function = None
    
    def infer_type(self, node: ASTNode) -> str:
        """Infer the type of an expression"""
        if isinstance(node, Literal):
            return node.literal_type
        
        elif isinstance(node, Identifier):
            if node.name not in self.symbol_table:
                raise TypeCheckError(
                    f"Undefined variable '{node.name}'",
                    node.line
                )
            return self.symbol_table[node.name]
        
        elif isinstance(node, BinaryOp):
            left_type = self.infer_type(node.left)
            right_type = self.infer_type(node.right)
            
            # Arithmetic operations
            if node.operator in ['+', '-', '*', '/', '%']:
                if left_type in ['int', 'float'] and right_type in ['int', 'float']:
                    # If either is float, result is float
                    return 'float' if 'float' in [left_type, right_type] else 'int'
                else:
                    raise TypeCheckError(
                        f"Binary operation '{node.operator}' not supported between '{left_type}' and '{right_type}'",
                        node.line
                    )
            
            # Comparison operations return int (used as boolean)
            elif node.operator in ['<', '>', '<=', '>=', '==', '!=']:
                if left_type in ['int', 'float'] and right_type in ['int', 'float']:
                    return 'int'
                else:
                    raise TypeCheckError(
                        f"Comparison '{node.operator}' not supported between '{left_type}' and '{right_type}'",
                        node.line
                    )
            
            # Logical operations
            elif node.operator in ['&&', '||']:
                return 'int'
            
            return left_type  # Default
        
        elif isinstance(node, UnaryOp):
            operand_type = self.infer_type(node.operand)
            if node.operator in ['++', '--']:
                if operand_type not in ['int', 'float']:
                    raise TypeCheckError(
                        f"Unary operation '{node.operator}' requires numeric type, got '{operand_type}'",
                        node.line
                    )
            return operand_type
        
        elif isinstance(node, ArrayAccess):
            array_type = self.infer_type(node.array)
            if not array_type.endswith('[]'):
                raise TypeCheckError(
                    f"Cannot index into non-array type '{array_type}'",
                    node.line
                )
            
            index_type = self.infer_type(node.index)
            if index_type != 'int':
                raise TypeCheckError(
                    f"Array index must be 'int', got '{index_type}'",
                    node.line
                )
            
            # Return element type
            return array_type[:-2]  # Remove []
        
        elif isinstance(node, MemberAccess):
            # Simplified - just pass through the base type
            base_type = self.infer_type(node.object)
            # For now, assume members have same type as base
            return 'int'  # Default
        
        # Default fallback
        return 'int'
    
    def types_compatible(self, target_type: str, value_type: str) -> bool:
        """Check if types are compatible for assignment"""
        if target_type == value_type:
            return True
        
        # int and float are somewhat compatible
        if target_type == 'float' and value_type == 'int':
            return True
        
        return False
