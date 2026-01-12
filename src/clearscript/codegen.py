"""
Code Generator for ClearScript

Generates InfiltrationEngine StateScript from ClearScript AST.
"""

from typing import List, Set
from .ast_nodes import *


class CodeGenerator:
    """Generates StateScript code from ClearScript AST."""
    
    def __init__(self, ast: Program):
        """Initialize the code generator."""
        self.ast = ast
        self.output = []
        self.label_counter = 0
        self.init_statements = []  # Top-level INIT statements
        self.function_labels = {}  # Map function names to labels
        
    def generate_label(self, prefix: str = "label") -> str:
        """Generate a unique label."""
        self.label_counter += 1
        return f"_{prefix}_{self.label_counter}"
    
    def generate(self) -> str:
        """Generate StateScript code from the AST."""
        self.output = []
        self.init_statements = []
        self.label_counter = 0
        
        # First pass: collect functions and top-level variable declarations
        functions = []
        main_statements = []
        
        for stmt in self.ast.statements:
            if isinstance(stmt, FunctionDeclaration):
                functions.append(stmt)
                self.function_labels[stmt.name] = stmt.name
            elif isinstance(stmt, VariableDeclaration):
                # Top-level variables become INIT
                self.init_statements.append(stmt)
            else:
                main_statements.append(stmt)
        
        # Output INIT statements first
        for init in self.init_statements:
            self.visit_init_declaration(init)
        
        # Add blank line after INITs if we have main code
        if self.init_statements and (main_statements or functions):
            self.output.append("")
        
        # Skip to main code
        if main_statements:
            self.output.append("GOTO _main")
            self.output.append("")
        
        # Output functions as labels
        for func in functions:
            self.visit_function_declaration(func)
            self.output.append("")
        
        # Output main code
        if main_statements:
            self.output.append(":_main")
            for stmt in main_statements:
                self.visit(stmt)
        
        return '\n'.join(self.output)
    
    def visit_init_declaration(self, node: VariableDeclaration):
        """Generate: INIT x 5"""
        if node.value:
            value_str = self.expression_to_string(node.value)
            self.output.append(f"INIT {node.name} {value_str}")
        else:
            self.output.append(f"INIT {node.name} 0")
    
    def visit_function_declaration(self, node: FunctionDeclaration):
        """Generate label and function body with POP for parameters."""
        self.output.append(f":{node.name}")
        
        # POP parameters in reverse order (stack semantics)
        for param in reversed(node.params):
            self.output.append(f"POP {param}")
        
        # Generate function body
        for stmt in node.body:
            self.visit(stmt)
        
        # Add RETURN if not already present
        if not node.body or not isinstance(node.body[-1], ReturnStatement):
            self.output.append("RETURN")
    
    def visit(self, node: ASTNode):
        """Dispatch to the appropriate visitor method."""
        if isinstance(node, VariableDeclaration):
            self.visit_variable_declaration(node)
        elif isinstance(node, ArrayDeclaration):
            self.visit_array_declaration(node)
        elif isinstance(node, Assignment):
            self.visit_assignment(node)
        elif isinstance(node, FunctionDeclaration):
            self.visit_function_declaration(node)
        elif isinstance(node, ClassDeclaration):
            self.visit_class_declaration(node)
        elif isinstance(node, StructDeclaration):
            self.visit_struct_declaration(node)
        elif isinstance(node, LabelDeclaration):
            self.visit_label_declaration(node)
        elif isinstance(node, GotoStatement):
            self.visit_goto_statement(node)
        elif isinstance(node, IfStatement):
            self.visit_if_statement(node)
        elif isinstance(node, WhileStatement):
            self.visit_while_statement(node)
        elif isinstance(node, ForLoop):
            self.visit_for_loop(node)
        elif isinstance(node, SwitchStatement):
            self.visit_switch_statement(node)
        elif isinstance(node, ConstDeclaration):
            self.visit_const_declaration(node)
        elif isinstance(node, ReturnStatement):
            self.visit_return_statement(node)
        elif isinstance(node, ExpressionStatement):
            self.visit_expression_statement(node)
        elif isinstance(node, RawBlock):
            self.visit_raw_block(node)
        elif isinstance(node, Comment):
            self.visit_comment(node)
        else:
            raise ValueError(f"Unknown node type: {type(node)}")
    
    def visit_variable_declaration(self, node: VariableDeclaration):
        """Generate: SET x 5 (for non-top-level variables)"""
        if node.value:
            value_str = self.expression_to_string(node.value)
            self.output.append(f"SET {node.name} {value_str}")
        else:
            self.output.append(f"SET {node.name} 0")
    
    def visit_array_declaration(self, node: ArrayDeclaration):
        """Generate array as indexed variables: arr_0, arr_1, arr_2, etc."""
        if node.initializer and isinstance(node.initializer, ArrayLiteral):
            # Generate indexed variables for each element
            for i, elem in enumerate(node.initializer.elements):
                value_str = self.expression_to_string(elem)
                self.output.append(f"SET {node.name}_{i} {value_str}")
            # Store array length
            self.output.append(f"SET {node.name}_length {len(node.initializer.elements)}")
        else:
            # No initializer, just set length to 0
            self.output.append(f"SET {node.name}_length 0")
    
    def visit_assignment(self, node: Assignment):
        """Generate: SET x value"""
        value_str = self.expression_to_string(node.value)
        self.output.append(f"SET {node.target} {value_str}")
    
    def visit_member_assignment(self, object_name: str, member_name: str, value):
        """Handle member assignment: obj.prop = value -> obj_prop = value"""
        value_str = self.expression_to_string(value)
        self.output.append(f"SET {object_name}_{member_name} {value_str}")
    
    def visit_label_declaration(self, node: LabelDeclaration):
        """Generate: :labelname"""
        self.output.append(f":{node.name}")
    
    def visit_goto_statement(self, node: GotoStatement):
        """Generate: GOTO label or GOTO label {condition}"""
        if node.condition:
            cond_str = self.expression_to_string(node.condition)
            self.output.append(f"GOTO {node.label} {{{cond_str}}}")
        else:
            self.output.append(f"GOTO {node.label}")
    
    def visit_if_statement(self, node: IfStatement):
        """Generate if/else using CALLIF pattern."""
        then_label = self.generate_label("if_then")
        end_label = self.generate_label("if_end")
        
        cond_str = self.expression_to_string(node.condition)
        
        if node.else_body:
            else_label = self.generate_label("if_else")
            
            # CALLIF for then branch
            self.output.append(f"CALLIF {then_label} {{{cond_str}}}")
            # CALL for else branch
            self.output.append(f"CALL {else_label}")
            self.output.append(f"GOTO {end_label}")
            
            # Then branch
            self.output.append(f":{then_label}")
            for stmt in node.then_body:
                self.visit(stmt)
            self.output.append("RETURN")
            
            # Else branch
            self.output.append(f":{else_label}")
            for stmt in node.else_body:
                self.visit(stmt)
            self.output.append("RETURN")
            
            # End label
            self.output.append(f":{end_label}")
        else:
            # Just CALLIF for then branch
            self.output.append(f"CALLIF {then_label} {{{cond_str}}}")
            self.output.append(f"GOTO {end_label}")
            
            # Then branch
            self.output.append(f":{then_label}")
            for stmt in node.then_body:
                self.visit(stmt)
            self.output.append("RETURN")
            
            # End label
            self.output.append(f":{end_label}")
    
    def visit_while_statement(self, node: WhileStatement):
        """Generate while loop using GOTO pattern."""
        loop_label = self.generate_label("while")
        end_label = self.generate_label("while_end")
        
        cond_str = self.expression_to_string(node.condition)
        
        # Loop start
        self.output.append(f":{loop_label}")
        # Exit if condition is false
        self.output.append(f"GOTO {end_label} {{!({cond_str})}}")
        
        # Loop body
        for stmt in node.body:
            self.visit(stmt)
        
        # Jump back to start
        self.output.append(f"GOTO {loop_label}")
        
        # End label
        self.output.append(f":{end_label}")
    
    def visit_for_loop(self, node: ForLoop):
        """Generate for loop as while loop: for(init; cond; inc) -> init; while(cond){body; inc}"""
        # Generate init statement
        if node.init:
            if isinstance(node.init, VariableDeclaration):
                self.visit_variable_declaration(node.init)
            else:
                # It's an expression/assignment
                expr_str = self.expression_to_string(node.init)
                self.output.append(expr_str)
        
        # Generate while loop
        loop_label = self.generate_label("for")
        end_label = self.generate_label("for_end")
        
        # Loop start
        self.output.append(f":{loop_label}")
        
        # Exit if condition is false
        if node.condition:
            cond_str = self.expression_to_string(node.condition)
            self.output.append(f"GOTO {end_label} {{!({cond_str})}}")
        
        # Loop body
        for stmt in node.body:
            self.visit(stmt)
        
        # Increment
        if node.increment:
            if isinstance(node.increment, UnaryOp) and node.increment.operator in ['++', '--']:
                # Handle increment/decrement specially
                operand_str = self.expression_to_string(node.increment.operand)
                if node.increment.operator == '++':
                    self.output.append(f"INC {operand_str}")
                else:
                    self.output.append(f"DEC {operand_str}")
            else:
                # Generic expression
                expr_str = self.expression_to_string(node.increment)
                if '=' in str(type(node.increment)):
                    # It's an assignment
                    self.output.append(expr_str)
                else:
                    # Evaluate expression (probably assignment inside)
                    pass
        
        # Jump back to start
        self.output.append(f"GOTO {loop_label}")
        
        # End label
        self.output.append(f":{end_label}")
    
    def visit_switch_statement(self, node: SwitchStatement):
        """Generate switch as if-else chain"""
        expr_str = self.expression_to_string(node.expression)
        end_label = self.generate_label("switch_end")
        
        # Generate if-else chain for cases
        for i, case in enumerate(node.cases):
            case_label = self.generate_label(f"case")
            next_label = self.generate_label(f"case_check")
            
            # Check if expression matches case value
            case_value_str = self.expression_to_string(case.value)
            self.output.append(f"CALLIF {case_label} {{{expr_str} == {case_value_str}}}")
            self.output.append(f"GOTO {next_label}")
            
            # Case body
            self.output.append(f":{case_label}")
            for stmt in case.statements:
                self.visit(stmt)
            self.output.append(f"GOTO {end_label}")
            
            # Next case check
            self.output.append(f":{next_label}")
        
            for stmt in node.default_case.statements:
                self.visit(stmt)
        
        # End label
        self.output.append(f":{end_label}")
    
    def visit_const_declaration(self, node: ConstDeclaration):
        """Generate const as regular variable (StateScript doesn't have const)"""
        if node.value:
            value_str = self.expression_to_string(node.value)
            self.output.append(f"SET {node.name} {value_str}")
        else:
            self.output.append(f"SET {node.name} 0")
    
    def visit_class_declaration(self, node: ClassDeclaration):
        """
        Transpile class to namespaced variables and prefixed methods.
        Classes are templates - they define structure but don't generate code directly.
        Instances would be created manually with namespaced variables.
        """
        # Classes don't generate output directly - they're templates
        # Actual instances would need manual variable creation
        # e.g., player1_health, player1_score
        # This is a design limitation due to StateScript's lack of OOP
        pass
    
    def visit_struct_declaration(self, node: StructDeclaration):
        """Transpile struct to namespaced variables (data-only)"""
        # Similar to classes - structs are templates
        # No code generation needed for the definition itself
        pass
    
    def visit_return_statement(self, node: ReturnStatement):
        """Generate: RETURN"""
        self.output.append("RETURN")
    
    def visit_expression_statement(self, node: ExpressionStatement):
        """Generate expression statement."""
        expr = node.expression
        
        # Handle special expressions that become statements
        if isinstance(expr, KillStatement):
            self.output.append("KILL")
        elif isinstance(expr, WaitStatement):
            time_str = self.expression_to_string(expr.time)
            if expr.result_var:
                self.output.append(f"WAIT {time_str} {expr.result_var}")
            else:
                self.output.append(f"WAIT {time_str}")
        elif isinstance(expr, WaitForStatement):
            cond_str = self.expression_to_string(expr.condition)
            self.output.append(f"WAITFOR {{{cond_str}}}")
        elif isinstance(expr, ThreadStatement):
            args_str = " ".join(self.expression_to_string(arg) for arg in expr.args)
            if args_str:
                self.output.append(f"THREAD {expr.label} {args_str}")
            else:
                self.output.append(f"THREAD {expr.label}")
        elif isinstance(expr, SetStatement):
            value_str = self.expression_to_string(expr.value)
            self.output.append(f"SET {expr.variable} {value_str}")
        elif isinstance(expr, PushStatement):
            value_str = self.expression_to_string(expr.value)
            self.output.append(f"PUSH {value_str}")
        elif isinstance(expr, PopStatement):
            self.output.append(f"POP {expr.variable}")
        elif isinstance(expr, PeekStatement):
            self.output.append(f"PEEK {expr.variable}")
        elif isinstance(expr, SpawnBotCall):
            template_str = self.expression_to_string(expr.template)
            location_str = self.expression_to_string(expr.location)
            attrs_str = " ".join(self.expression_to_string(attr) for attr in expr.attributes)
            if attrs_str:
                self.output.append(f"SPAWNBOT {template_str} {location_str} {attrs_str}")
            else:
                self.output.append(f"SPAWNBOT {template_str} {location_str}")
        elif isinstance(expr, MoveToCall):
            prop_str = self.expression_to_string(expr.prop)
            location_str = self.expression_to_string(expr.location)
            self.output.append(f"MOVETO {prop_str} {location_str}")
        elif isinstance(expr, AnimateCall):
            prop_str = self.expression_to_string(expr.prop)
            location_str = self.expression_to_string(expr.location)
            time_str = self.expression_to_string(expr.time)
            self.output.append(f"ANIMATE {prop_str} {location_str} {time_str}")
        elif isinstance(expr, DeleteCall):
            prop_str = self.expression_to_string(expr.prop)
            self.output.append(f"DELETE {prop_str}")
        elif isinstance(expr, UnaryOp):
            # Handle increment/decrement as statements
            if expr.operator in ['++', '--']:
                operand_str = self.expression_to_string(expr.operand)
                if expr.operator == '++':
                    self.output.append(f"INC {operand_str}")
                else:
                    self.output.append(f"DEC {operand_str}")
            else:
                # Other unary ops as expressions
                expr_str = self.expression_to_string(expr)
                self.output.append(expr_str)
        elif isinstance(expr, Assignment):
            # Assignment as statement
            value_str = self.expression_to_string(expr.value)
            self.output.append(f"SET {expr.target} {value_str}")
        elif isinstance(expr, FunctionCall):
            # User function call - generate PUSH for each arg in reverse, then CALL
            for arg in reversed(expr.args):
                arg_str = self.expression_to_string(arg)
                self.output.append(f"PUSH {arg_str}")
            self.output.append(f"CALL {expr.name}")
        else:
            # Generic expression statement
            expr_str = self.expression_to_string(expr)
            self.output.append(expr_str)
    
    def visit_raw_block(self, node: RawBlock):
        """Output raw StateScript code directly."""
        if node.code:
            self.output.append(node.code)
    
    def visit_comment(self, node: Comment):
        """Generate comment."""
        if node.is_block:
            self.output.append(f"/* {node.text} */")
        else:
            self.output.append(f"// {node.text}")
    
    def expression_to_string(self, node: ASTNode) -> str:
        """Convert an expression node to a string with proper StateScript formatting."""
        if node is None:
            return ""
        
        if isinstance(node, Literal):
            if node.literal_type == 'string':
                # String literals wrapped in []
                return f"[{node.value}]"
            else:
                return str(node.value)
        
        elif isinstance(node, Identifier):
            return node.name
        
        elif isinstance(node, ArrayAccess):
            # Array access: arr[i] becomes arr_i if index is constant, or dynamic lookup
            if isinstance(node.array, Identifier):
                array_name = node.array.name
                # Try to get constant index
                if isinstance(node.index, Literal):
                    index_val = node.index.value
                    return f"{array_name}_{index_val}"
                elif isinstance(node.index, Identifier):
                    # Dynamic index - use variable name as suffix
                    index_name = node.index.name
                    # This is a limitation: StateScript doesn't support dynamic indexing
                    # We'll use a computed variable name pattern
                    return f"{{${array_name}_{{{index_name}}}}}"
                else:
                    # Complex expression as index
                    return f"{array_name}_0"  # Fallback
            return "unknown_array"
        
        elif isinstance(node, TernaryExpression):
            # Ternary not directly supported in expressions, convert to if-else conceptually
            # For now, just return a placeholder - proper support needs statement context
            cond_str = self.expression_to_string(node.condition)
            true_str = self.expression_to_string(node.true_value)
            false_str = self.expression_to_string(node.false_value)
            # Use inline conditional syntax if StateScript supports it, otherwise limitation
            return f"({cond_str} ? {true_str} : {false_str})"  # Placeholder
        
        elif isinstance(node, MemberAccess):
            # Member access: obj.property becomes obj_property
            if isinstance(node.object, Identifier):
                obj_name = node.object.name
                return f"{obj_name}_{node.member}"
            elif isinstance(node.object, MemberAccess):
                # Nested member access: obj.prop1.prop2
                obj_str = self.expression_to_string(node.object)
                return f"{obj_str}_{node.member}"
            else:
                return f"unknown_{node.member}"
        
        elif isinstance(node, FunctionCall):
            # Function calls in expression context are tricky
            # For now, just return the name - they should be statements
            # If needed in expression, would need temp variable
            return f"/* CALL {node.name} */"
        
        elif isinstance(node, BinaryOp):
            left = self.expression_to_string(node.left)
            right = self.expression_to_string(node.right)
            # Wrap in {} for StateScript expression
            return f"{{{left} {node.operator} {right}}}"
        
        elif isinstance(node, UnaryOp):
            operand = self.expression_to_string(node.operand)
            if node.is_postfix:
                return f"{{{operand}{node.operator}}}"
            else:
                return f"{{{node.operator}{operand}}}"
        
        elif isinstance(node, Assignment):
            # Assignment in expression context is unusual but handle it
            value = self.expression_to_string(node.value)
            return f"{node.target} = {value}"
        
        else:
            raise ValueError(f"Cannot convert {type(node)} to expression string")
