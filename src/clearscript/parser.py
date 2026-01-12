"""
Parser for ClearScript

Converts a stream of tokens into an Abstract Syntax Tree (AST).
Targets InfiltrationEngine's StateScript.
"""

from typing import List, Optional
from .lexer import Token, TokenType
from .ast_nodes import *


class ParseError(Exception):
    """Exception raised during parsing."""
    pass


class Parser:
    """Recursive descent parser for ClearScript."""
    
    def __init__(self, tokens: List[Token]):
        """Initialize the parser with a list of tokens."""
        self.tokens = tokens
        self.pos = 0
    
    def current_token(self) -> Token:
        """Get the current token."""
        if self.pos >= len(self.tokens):
            return self.tokens[-1]  # Return EOF
        return self.tokens[self.pos]
    
    def peek_token(self, offset: int = 1) -> Token:
        """Peek ahead at a token."""
        pos = self.pos + offset
        if pos >= len(self.tokens):
            return self.tokens[-1]  # Return EOF
        return self.tokens[pos]
    
    def advance(self) -> Token:
        """Consume and return the current token."""
        token = self.current_token()
        if self.pos < len(self.tokens) - 1:
            self.pos += 1
        return token
    
    def expect(self, token_type: TokenType) -> Token:
        """Expect a specific token type and advance."""
        token = self.current_token()
        if token.type != token_type:
            raise ParseError(
                f"Expected {token_type.name} but got {token.type.name} "
                f"at {token.line}:{token.column}"
           )
        return self.advance()
    
    def match(self, *token_types: TokenType) -> bool:
        """Check if current token matches any of the given types."""
        return self.current_token().type in token_types
    
    def skip_comments(self):
        """Skip comment tokens."""
        while self.match(TokenType.COMMENT):
            self.advance()
    
    def parse(self) -> Program:
        """Parse the entire program."""
        statements = []
        
        while not self.match(TokenType.EOF):
            self.skip_comments()
            if self.match(TokenType.EOF):
                break
            
            stmt = self.parse_statement()
            if stmt:
                statements.append(stmt)
        
        return Program(statements=statements)
    
    def parse_statement(self) -> Optional[ASTNode]:
        """Parse a single statement."""
        self.skip_comments()
        
        # Const declaration (treated as variable)
        if self.match(TokenType.CONST):
            const_token = self.advance()
            if not self.match(TokenType.INT, TokenType.FLOAT):
                raise ParseError("Expected type after const")
            type_token = self.advance()
            name_token = self.expect(TokenType.IDENTIFIER)
            self.expect(TokenType.ASSIGN)
            value = self.parse_expression()
            self.expect(TokenType.SEMICOLON)
            return ConstDeclaration(
                var_type=type_token.value,
                name=name_token.value,
                value=value,
                line=const_token.line,
                column=const_token.column
            )
        
        # Variable declaration (including arrays)
        if self.match(TokenType.INT, TokenType.FLOAT):
            return self.parse_variable_declaration()
        
        # Function declaration
        if self.match(TokenType.FUNCTION):
            return self.parse_function_declaration()
        
        # Class declaration
        if self.match(TokenType.CLASS):
            return self.parse_class_declaration()
        
        # Struct declaration
        if self.match(TokenType.STRUCT):
            return self.parse_struct_declaration()
        
        # Label declaration
        if self.match(TokenType.LABEL):
            return self.parse_label_declaration()
        
        # Goto statement
        if self.match(TokenType.GOTO):
            return self.parse_goto_statement()
        
        # If statement
        if self.match(TokenType.IF):
            return self.parse_if_statement()
        
        # While statement
        if self.match(TokenType.WHILE):
            return self.parse_while_statement()
        
        # For loop
        if self.match(TokenType.FOR):
            return self.parse_for_loop()
        
        # Switch statement
        if self.match(TokenType.SWITCH):
            return self.parse_switch_statement()
        
        # Return statement
        if self.match(TokenType.RETURN):
            return self.parse_return_statement()
        
        # Simple statement keywords
        if self.match(TokenType.KILL):
            return self.parse_kill_statement()
        
        if self.match(TokenType.WAIT):
            return self.parse_wait_statement()
        
        if self.match(TokenType.WAITFOR):
            return self.parse_waitfor_statement()
        
        if self.match(TokenType.THREAD):
            return self.parse_thread_statement()
        
        # Check if these are function calls (followed by '(') or statements
        if self.match(TokenType.SET):
            if self.peek_token().type == TokenType.LPAREN:
                return self.parse_set_statement()
            # Otherwise it's used as identifier in expression
            return self.parse_expression_statement()
        
        if self.match(TokenType.PUSH):
            if self.peek_token().type == TokenType.LPAREN:
                return self.parse_push_statement()
            return self.parse_expression_statement()
        
        if self.match(TokenType.POP):
            if self.peek_token().type == TokenType.LPAREN:
                return self.parse_pop_statement()
            return self.parse_expression_statement()
        
        if self.match(TokenType.PEEK):
            if self.peek_token().type == TokenType.LPAREN:
                return self.parse_peek_statement()
            return self.parse_expression_statement()
        
        # Built-in function calls
        if self.match(TokenType.SPAWNBOT, TokenType.MOVETO, TokenType.ANIMATE, TokenType.DELETE):
            return self.parse_builtin_call()
        
        # Raw StateScript block
        if self.match(TokenType.RAW):
            return self.parse_raw_block()
        
        # Assignment or expression statement
        return self.parse_expression_statement()
    
    def parse_raw_block(self) -> RawBlock:
        """Parse: raw { ... } - allows direct StateScript injection."""
        raw_token = self.advance()  # Skip 'raw'
        self.expect(TokenType.LBRACE)
        
        # Collect everything until the closing brace
        raw_code = []
        brace_count = 1
        
        while brace_count > 0 and not self.match(TokenType.EOF):
            token = self.current_token()
            
            if token.type == TokenType.LBRACE:
                brace_count += 1
                raw_code.append('{')
            elif token.type == TokenType.RBRACE:
                brace_count -= 1
                if brace_count > 0:
                    raw_code.append('}')
            else:
                # Add token value as-is
                if token.type == TokenType.IDENTIFIER or token.type in [
                    TokenType.INT, TokenType.FLOAT, TokenType.FUNCTION, TokenType.GOTO,
                    TokenType.LABEL, TokenType.WAIT, TokenType.KILL, TokenType.SET,
                    TokenType.PUSH, TokenType.POP, TokenType.PEEK, TokenType.SPAWNBOT,
                    TokenType.MOVETO, TokenType.ANIMATE, TokenType.DELETE
                ]:
                    raw_code.append(str(token.value))
                elif token.type == TokenType.NUMBER:
                    raw_code.append(str(token.value))
                elif token.type == TokenType.STRING:
                    raw_code.append(f'[{token.value}]')
                elif token.value:
                    raw_code.append(str(token.value))
            
            self.advance()
        
        return RawBlock(
            code=' '.join(raw_code).strip(),
            line=raw_token.line,
            column=raw_token.column
        )
    
    def parse_variable_declaration(self) -> VariableDeclaration:
        """Parse: int x = 5; or int[] arr = [1, 2, 3];"""
        type_token = self.advance()
        var_type = type_token.value
        
        # Check for array type: int[]
        is_array = False
        if self.match(TokenType.LBRACKET):
            self.advance()  # Skip [
            self.expect(TokenType.RBRACKET)  # Expect ]
            is_array = True
        
        name_token = self.expect(TokenType.IDENTIFIER)
        name = name_token.value
        
        value = None
        if self.match(TokenType.ASSIGN):
            self.advance()
            value = self.parse_expression()
        
        self.expect(TokenType.SEMICOLON)
        
        if is_array:
            return ArrayDeclaration(
                elem_type=var_type,
                name=name,
                initializer=value,
                line=type_token.line,
                column=type_token.column
            )
        else:
            return VariableDeclaration(
                var_type=var_type,
                name=name,
                value=value,
                line=type_token.line,
                column=type_token.column
            )
    
    def parse_function_declaration(self) -> FunctionDeclaration:
        """Parse: function name(param1, param2) { ... }"""
        func_token = self.advance()  # Skip 'function'
        
        name_token = self.expect(TokenType.IDENTIFIER)
        name = name_token.value
        
        self.expect(TokenType.LPAREN)
        params = []
        
        while not self.match(TokenType.RPAREN):
            param_token = self.expect(TokenType.IDENTIFIER)
            params.append(param_token.value)
            
            if self.match(TokenType.COMMA):
                self.advance()
        
        self.expect(TokenType.RPAREN)
        self.expect(TokenType.LBRACE)
        body = self.parse_block()
        self.expect(TokenType.RBRACE)
        
        return FunctionDeclaration(
            name=name,
            params=params,
            body=body,
            line=func_token.line,
            column=func_token.column
        )
    
    def parse_class_declaration(self) -> ClassDeclaration:
        """Parse: class Name { properties... methods... }"""
        class_token = self.advance()  # Skip 'class'
        name_token = self.expect(TokenType.IDENTIFIER)
        name = name_token.value
        
        self.expect(TokenType.LBRACE)
        
        properties = []
        methods = []
        
        while not self.match(TokenType.RBRACE):
            # Check for method
            if self.match(TokenType.METHOD):
                methods.append(self.parse_method_declaration())
            # Check for property (variable declaration)
            elif self.match(TokenType.INT, TokenType.FLOAT):
                prop = self.parse_variable_declaration()
                properties.append(prop)
            else:
                raise ParseError(f"Unexpected token in class body: {self.current_token().type}")
        
        self.expect(TokenType.RBRACE)
        
        return ClassDeclaration(
            name=name,
            properties=properties,
            methods=methods,
            line=class_token.line,
            column=class_token.column
        )
    
    def parse_struct_declaration(self) -> StructDeclaration:
        """Parse: struct Name { properties... }"""
        struct_token = self.advance()  # Skip 'struct'
        name_token = self.expect(TokenType.IDENTIFIER)
        name = name_token.value
        
        self.expect(TokenType.LBRACE)
        
        properties = []
        
        while not self.match(TokenType.RBRACE):
            if self.match(TokenType.INT, TokenType.FLOAT):
                prop = self.parse_variable_declaration()
                properties.append(prop)
            else:
                raise ParseError(f"Unexpected token in struct body: {self.current_token().type}")
        
        self.expect(TokenType.RBRACE)
        
        return StructDeclaration(
            name=name,
            properties=properties,
            line=struct_token.line,
            column=struct_token.column
        )
    
    def parse_method_declaration(self) -> MethodDeclaration:
        """Parse: method name(params) { body }"""
        method_token = self.advance()  # Skip 'method'
        name_token = self.expect(TokenType.IDENTIFIER)
        name = name_token.value
        
        self.expect(TokenType.LPAREN)
        params = []
        
        while not self.match(TokenType.RPAREN):
            param_token = self.expect(TokenType.IDENTIFIER)
            params.append(param_token.value)
            if self.match(TokenType.COMMA):
                self.advance()
        
        self.expect(TokenType.RPAREN)
        self.expect(TokenType.LBRACE)
        body = self.parse_block()
        self.expect(TokenType.RBRACE)
        
        return MethodDeclaration(
            name=name,
            params=params,
            body=body,
            line=method_token.line,
            column=method_token.column
        )
    
    def parse_label_declaration(self) -> LabelDeclaration:
        """Parse: label: name"""
        label_token = self.advance()  # Skip 'label'
        self.expect(TokenType.COLON)
        
        name_token = self.expect(TokenType.IDENTIFIER)
        name = name_token.value
        
        return LabelDeclaration(
            name=name,
            line=label_token.line,
            column=label_token.column
        )
    
    def parse_goto_statement(self) -> GotoStatement:
        """Parse: goto label; or goto label if (condition);"""
        goto_token = self.advance()  # Skip 'goto'
        
        label_token = self.expect(TokenType.IDENTIFIER)
        label = label_token.value
        
        condition = None
        if self.match(TokenType.IF):
            self.advance()
            self.expect(TokenType.LPAREN)
            condition = self.parse_expression()
            self.expect(TokenType.RPAREN)
        
        self.expect(TokenType.SEMICOLON)
        
        return GotoStatement(
            label=label,
            condition=condition,
            line=goto_token.line,
            column=goto_token.column
        )
    
    def parse_kill_statement(self) -> ExpressionStatement:
        """Parse: kill();"""
        kill_token = self.advance()
        self.expect(TokenType.LPAREN)
        self.expect(TokenType.RPAREN)
        self.expect(TokenType.SEMICOLON)
        
        return ExpressionStatement(
            expression=KillStatement(line=kill_token.line, column=kill_token.column),
            line=kill_token.line,
            column=kill_token.column
        )
    
    def parse_return_statement(self) -> ReturnStatement:
        """Parse: return;"""
        return_token = self.advance()
        self.expect(TokenType.SEMICOLON)
        
        return ReturnStatement(
            line=return_token.line,
            column=return_token.column
        )
    
    def parse_wait_statement(self) -> ExpressionStatement:
        """Parse: wait(time);"""
        wait_token = self.advance()
        self.expect(TokenType.LPAREN)
        time = self.parse_expression()
        self.expect(TokenType.RPAREN)
        self.expect(TokenType.SEMICOLON)
        
        return ExpressionStatement(
            expression=WaitStatement(time=time, line=wait_token.line, column=wait_token.column),
            line=wait_token.line,
            column=wait_token.column
        )
    
    def parse_waitfor_statement(self) -> ExpressionStatement:
        """Parse: waitfor(condition);"""
        waitfor_token = self.advance()
        self.expect(TokenType.LPAREN)
        condition = self.parse_expression()
        self.expect(TokenType.RPAREN)
        self.expect(TokenType.SEMICOLON)
        
        return ExpressionStatement(
            expression=WaitForStatement(condition=condition, line=waitfor_token.line, column=waitfor_token.column),
            line=waitfor_token.line,
            column=waitfor_token.column
        )
    
    def parse_thread_statement(self) -> ExpressionStatement:
        """Parse: thread(label, arg1, arg2);"""
        thread_token = self.advance()
        self.expect(TokenType.LPAREN)
        
        label_token = self.expect(TokenType.IDENTIFIER)
        label = label_token.value
        
        args = []
        while self.match(TokenType.COMMA):
            self.advance()
            args.append(self.parse_expression())
        
        self.expect(TokenType.RPAREN)
        self.expect(TokenType.SEMICOLON)
        
        return ExpressionStatement(
            expression=ThreadStatement(label=label, args=args, line=thread_token.line, column=thread_token.column),
            line=thread_token.line,
            column=thread_token.column
        )
    
    def parse_set_statement(self) -> ExpressionStatement:
        """Parse: set(var, value);"""
        set_token = self.advance()
        self.expect(TokenType.LPAREN)
        
        var_token = self.expect(TokenType.IDENTIFIER)
        variable = var_token.value
        
        self.expect(TokenType.COMMA)
        value = self.parse_expression()
        
        self.expect(TokenType.RPAREN)
        self.expect(TokenType.SEMICOLON)
        
        return ExpressionStatement(
            expression=SetStatement(variable=variable, value=value, line=set_token.line, column=set_token.column),
            line=set_token.line,
            column=set_token.column
        )
    
    def parse_push_statement(self) -> ExpressionStatement:
        """Parse: push(value);"""
        push_token = self.advance()
        self.expect(TokenType.LPAREN)
        value = self.parse_expression()
        self.expect(TokenType.RPAREN)
        self.expect(TokenType.SEMICOLON)
        
        return ExpressionStatement(
            expression=PushStatement(value=value, line=push_token.line, column=push_token.column),
            line=push_token.line,
            column=push_token.column
        )
    
    def parse_pop_statement(self) -> ExpressionStatement:
        """Parse: pop(variable);"""
        pop_token = self.advance()
        self.expect(TokenType.LPAREN)
        
        var_token = self.expect(TokenType.IDENTIFIER)
        variable = var_token.value
        
        self.expect(TokenType.RPAREN)
        self.expect(TokenType.SEMICOLON)
        
        return ExpressionStatement(
            expression=PopStatement(variable=variable, line=pop_token.line, column=pop_token.column),
            line=pop_token.line,
            column=pop_token.column
        )
    
    def parse_peek_statement(self) -> ExpressionStatement:
        """Parse: peek(variable);"""
        peek_token = self.advance()
        self.expect(TokenType.LPAREN)
        
        var_token = self.expect(TokenType.IDENTIFIER)
        variable = var_token.value
        
        self.expect(TokenType.RPAREN)
        self.expect(TokenType.SEMICOLON)
        
        return ExpressionStatement(
            expression=PeekStatement(variable=variable, line=peek_token.line, column=peek_token.column),
            line=peek_token.line,
            column=peek_token.column
        )
    
    def parse_builtin_call(self) -> ExpressionStatement:
        """Parse built-in function calls like spawnbot, moveto, etc."""
        builtin_token = self.current_token()
        builtin_type = builtin_token.type
        self.advance()
        
        self.expect(TokenType.LPAREN)
        args = []
        
        while not self.match(TokenType.RPAREN):
            args.append(self.parse_expression())
            if self.match(TokenType.COMMA):
                self.advance()
        
        self.expect(TokenType.RPAREN)
        self.expect(TokenType.SEMICOLON)
        
        # Create appropriate node based on builtin type
        if builtin_type == TokenType.SPAWNBOT:
            node = SpawnBotCall(
                template=args[0] if len(args) > 0 else None,
                location=args[1] if len(args) > 1 else None,
                attributes=args[2:] if len(args) > 2 else [],
                line=builtin_token.line,
                column=builtin_token.column
            )
        elif builtin_type == TokenType.MOVETO:
            node = MoveToCall(
                prop=args[0] if len(args) > 0 else None,
                location=args[1] if len(args) > 1 else None,
                line=builtin_token.line,
                column=builtin_token.column
            )
        elif builtin_type == TokenType.ANIMATE:
            node = AnimateCall(
                prop=args[0] if len(args) > 0 else None,
                location=args[1] if len(args) > 1 else None,
                time=args[2] if len(args) > 2 else None,
                line=builtin_token.line,
                column=builtin_token.column
            )
        elif builtin_type == TokenType.DELETE:
            node = DeleteCall(
                prop=args[0] if len(args) > 0 else None,
                line=builtin_token.line,
                column=builtin_token.column
            )
        else:
            raise ParseError(f"Unknown builtin: {builtin_type}")
        
        return ExpressionStatement(
            expression=node,
            line=builtin_token.line,
            column=builtin_token.column
        )
    
    def parse_for_loop(self) -> ForLoop:
        """Parse: for (init; condition; increment) { body }"""
        for_token = self.advance()  # Skip 'for'
        self.expect(TokenType.LPAREN)
        
        # Parse init (can be variable declaration or expression/assignment)
        init = None
        if not self.match(TokenType.SEMICOLON):
            if self.match(TokenType.INT, TokenType.FLOAT):
                # For loop variable declaration - parse inline without semicolon
                type_token = self.advance()
                var_type = type_token.value
                name_token = self.expect(TokenType.IDENTIFIER)
                name = name_token.value
                value = None
                if self.match(TokenType.ASSIGN):
                    self.advance()
                    value = self.parse_expression()
                init = VariableDeclaration(
                    var_type=var_type,
                    name=name,
                    value=value,
                    line=type_token.line,
                    column=type_token.column
                )
            else:
                init = self.parse_expression()
        self.expect(TokenType.SEMICOLON)
        
        # Parse condition
        condition = None
        if not self.match(TokenType.SEMICOLON):
            condition = self.parse_expression()
        self.expect(TokenType.SEMICOLON)
        
        # Parse increment
        increment = None
        if not self.match(TokenType.RPAREN):
            increment = self.parse_expression()
        self.expect(TokenType.RPAREN)
        
        # Parse body
        self.expect(TokenType.LBRACE)
        body = self.parse_block()
        self.expect(TokenType.RBRACE)
        
        return ForLoop(
            init=init,
            condition=condition,
            increment=increment,
            body=body,
            line=for_token.line,
            column=for_token.column
        )
    
    def parse_switch_statement(self) -> SwitchStatement:
        """Parse: switch (expr) { case val: ... default: ... }"""
        switch_token = self.advance()  # Skip 'switch'
        self.expect(TokenType.LPAREN)
        expression = self.parse_expression()
        self.expect(TokenType.RPAREN)
        self.expect(TokenType.LBRACE)
        
        cases = []
        default_case = None
        
        while not self.match(TokenType.RBRACE):
            if self.match(TokenType.CASE):
                case_token = self.advance()  # Skip 'case'
                value = self.parse_expression()
                self.expect(TokenType.COLON)
                
                # Parse statements until next case/default/break/}
                statements = []
                while not self.match(TokenType.CASE, TokenType.DEFAULT, TokenType.RBRACE):
                    if self.match(TokenType.BREAK):
                        self.advance()
                        self.expect(TokenType.SEMICOLON)
                        break
                    stmt = self.parse_statement()
                    if stmt:
                        statements.append(stmt)
                
                cases.append(CaseStatement(
                    value=value,
                    statements=statements,
                    line=case_token.line,
                    column=case_token.column
                ))
            
            elif self.match(TokenType.DEFAULT):
                default_token = self.advance()  # Skip 'default'
                self.expect(TokenType.COLON)
                
                # Parse statements until }
                statements = []
                while not self.match(TokenType.RBRACE):
                    if self.match(TokenType.BREAK):
                        self.advance()
                        self.expect(TokenType.SEMICOLON)
                        break
                    stmt = self.parse_statement()
                    if stmt:
                        statements.append(stmt)
                
                default_case = DefaultCase(
                    statements=statements,
                    line=default_token.line,
                    column=default_token.column
                )
            else:
                break
        
        self.expect(TokenType.RBRACE)
        
        return SwitchStatement(
            expression=expression,
            cases=cases,
            default_case=default_case,
            line=switch_token.line,
            column=switch_token.column
        )
    
    def parse_if_statement(self) -> IfStatement:
        """Parse: if (condition) { ... } else { ... }"""
        if_token = self.advance()  # Skip 'if'
        
        self.expect(TokenType.LPAREN)
        condition = self.parse_expression()
        self.expect(TokenType.RPAREN)
        
        self.expect(TokenType.LBRACE)
        then_body = self.parse_block()
        self.expect(TokenType.RBRACE)
        
        else_body = None
        if self.match(TokenType.ELSE):
            self.advance()  # Skip 'else'
            self.expect(TokenType.LBRACE)
            else_body = self.parse_block()
            self.expect(TokenType.RBRACE)
        
        return IfStatement(
            condition=condition,
            then_body=then_body,
            else_body=else_body,
            line=if_token.line,
            column=if_token.column
        )
    
    def parse_while_statement(self) -> WhileStatement:
        """Parse: while (condition) { ... }"""
        while_token = self.advance()  # Skip 'while'
        
        self.expect(TokenType.LPAREN)
        condition = self.parse_expression()
        self.expect(TokenType.RPAREN)
        
        self.expect(TokenType.LBRACE)
        body = self.parse_block()
        self.expect(TokenType.RBRACE)
        
        return WhileStatement(
            condition=condition,
            body=body,
            line=while_token.line,
            column=while_token.column
        )
    
    def parse_block(self) -> List[ASTNode]:
        """Parse a block of statements."""
        statements = []
        
        while not self.match(TokenType.RBRACE, TokenType.EOF):
            self.skip_comments()
            if self.match(TokenType.RBRACE, TokenType.EOF):
                break
            
            stmt = self.parse_statement()
            if stmt:
                statements.append(stmt)
        
        return statements
    
    def parse_expression_statement(self) -> ExpressionStatement:
        """Parse an expression followed by a semicolon."""
        expr = self.parse_expression()
        self.expect(TokenType.SEMICOLON)
        
        return ExpressionStatement(
            expression=expr,
            line=expr.line if hasattr(expr, 'line') else 0,
            column=expr.column if hasattr(expr, 'column') else 0
        )
    
    # Expression parsing remains the same
    def parse_expression(self) -> ASTNode:
        """Parse an expression."""
        return self.parse_ternary()
    
    def parse_ternary(self) -> ASTNode:
        """Parse ternary operator: condition ? true_val : false_val"""
        expr = self.parse_logical_or()
        
        if self.match(TokenType.QUESTION):
            self.advance()  # Skip ?
            true_value = self.parse_expression()
            self.expect(TokenType.COLON)
            false_value = self.parse_expression()
            return TernaryExpression(
                condition=expr,
                true_value=true_value,
                false_value=false_value,
                line=expr.line if hasattr(expr, 'line') else 0,
                column=expr.column if hasattr(expr, 'column') else 0
            )
        
        return expr
    
    def parse_logical_or(self) -> ASTNode:
        """Parse logical OR: a || b"""
        left = self.parse_logical_and()
        
        while self.match(TokenType.OR):
            op_token = self.advance()
            right = self.parse_logical_and()
            left = BinaryOp(
                left=left,
                operator=op_token.value,
                right=right,
                line=op_token.line,
                column=op_token.column
            )
        
        return left
    
    def parse_logical_and(self) -> ASTNode:
        """Parse logical AND: a && b"""
        left = self.parse_equality()
        
        while self.match(TokenType.AND):
            op_token = self.advance()
            right = self.parse_equality()
            left = BinaryOp(
                left=left,
                operator=op_token.value,
                right=right,
                line=op_token.line,
                column=op_token.column
            )
        
        return left
    
    def parse_equality(self) -> ASTNode:
        """Parse equality: a == b, a != b"""
        left = self.parse_comparison()
        
        while self.match(TokenType.EQ, TokenType.NEQ):
            op_token = self.advance()
            right = self.parse_comparison()
            left = BinaryOp(
                left=left,
                operator=op_token.value,
                right=right,
                line=op_token.line,
                column=op_token.column
            )
        
        return left
    
    def parse_comparison(self) -> ASTNode:
        """Parse comparison: a < b, a > b, a <= b, a >= b"""
        left = self.parse_additive()
        
        while self.match(TokenType.LT, TokenType.GT, TokenType.LTE, TokenType.GTE):
            op_token = self.advance()
            right = self.parse_additive()
            left = BinaryOp(
                left=left,
                operator=op_token.value,
                right=right,
                line=op_token.line,
                column=op_token.column
            )
        
        return left
    
    def parse_additive(self) -> ASTNode:
        """Parse addition/subtraction: a + b, a - b"""
        left = self.parse_multiplicative()
        
        while self.match(TokenType.PLUS, TokenType.MINUS):
            op_token = self.advance()
            right = self.parse_multiplicative()
            left = BinaryOp(
                left=left,
                operator=op_token.value,
                right=right,
                line=op_token.line,
                column=op_token.column
            )
        
        return left
    
    def parse_multiplicative(self) -> ASTNode:
        """Parse multiplication/division: a * b, a / b"""
        left = self.parse_unary()
        
        while self.match(TokenType.MULTIPLY, TokenType.DIVIDE):
            op_token = self.advance()
            right = self.parse_unary()
            left = BinaryOp(
                left=left,
                operator=op_token.value,
                right=right,
                line=op_token.line,
                column=op_token.column
            )
        
        return left
    
    def parse_unary(self) -> ASTNode:
        """Parse unary operators: !x, -x, ++x, --x"""
        if self.match(TokenType.NOT, TokenType.MINUS, TokenType.INCREMENT, TokenType.DECREMENT):
            op_token = self.advance()
            operand = self.parse_unary()
            return UnaryOp(
                operator=op_token.value,
                operand=operand,
                is_postfix=False,
                line=op_token.line,
                column=op_token.column
            )
        
        return self.parse_postfix()
    
    def parse_postfix(self) -> ASTNode:
        """Parse postfix operators and function calls."""
        expr = self.parse_primary()
        
        while True:
            # Array indexing: arr[index]
            if self.match(TokenType.LBRACKET):
                self.advance()  # Skip [
                index = self.parse_expression()
                self.expect(TokenType.RBRACKET)
                expr = ArrayAccess(
                    array=expr,
                    index=index,
                    line=expr.line if hasattr(expr, 'line') else 0,
                    column=expr.column if hasattr(expr, 'column') else 0
                )
            
            # Member access: obj.property
            elif self.match(TokenType.DOT):
                self.advance()  # Skip .
                member_token = self.expect(TokenType.IDENTIFIER)
                expr = MemberAccess(
                    object=expr,
                    member=member_token.value,
                    line=expr.line if hasattr(expr, 'line') else 0,
                    column=expr.column if hasattr(expr, 'column') else 0
                )
            
            # Function call
            elif self.match(TokenType.LPAREN):
                self.advance()  # Skip (
                args = []
                
                while not self.match(TokenType.RPAREN):
                    args.append(self.parse_expression())
                    if self.match(TokenType.COMMA):
                        self.advance()
                
                self.expect(TokenType.RPAREN)
                
                # Convert identifier to function call
                if isinstance(expr, Identifier):
                    expr = FunctionCall(
                        name=expr.name,
                        args=args,
                        line=expr.line,
                        column=expr.column
                    )
                else:
                    raise ParseError("Only identifiers can be called as functions")
                
            # Postfix increment/decrement
            elif self.match(TokenType.INCREMENT, TokenType.DECREMENT):
                op_token = self.advance()
                expr = UnaryOp(
                    operator=op_token.value,
                    operand=expr,
                    is_postfix=True,
                    line=op_token.line,
                    column=op_token.column
                )
            
            else:
                break
        
        # Check for simple assignment
        if self.match(TokenType.ASSIGN):
            self.advance()  # Skip =
            value = self.parse_expression()
            
            if isinstance(expr, Identifier):
                expr = Assignment(
                    target=expr.name,
                    value=value,
                    line=expr.line,
                    column=expr.column
                )
            else:
                raise ParseError("Invalid assignment target")
        
        return expr
    
    def parse_primary(self) -> ASTNode:
        """Parse primary expressions: literals, identifiers, parenthesized expressions"""
        token = self.current_token()
        
        # Number literal
        if self.match(TokenType.NUMBER):
            self.advance()
            literal_type = 'float' if isinstance(token.value, float) else 'int'
            return Literal(
                value=token.value,
                literal_type=literal_type,
                line=token.line,
                column=token.column
            )
        
        # String literal
        if self.match(TokenType.STRING):
            self.advance()
            return Literal(
                value=token.value,
                literal_type='string',
                line=token.line,
                column=token.column
            )
        
        # Array literal: [1, 2, 3]
        if self.match(TokenType.LBRACKET):
            return self.parse_array_literal()
        
        # Identifier
        if self.match(TokenType.IDENTIFIER):
            self.advance()
            return Identifier(
                name=token.value,
                line=token.line,
                column=token.column
            )
        
        # Parenthesized expression
        if self.match(TokenType.LPAREN):
            self.advance()  # Skip (
            expr = self.parse_expression()
            self.expect(TokenType.RPAREN)
            return expr
        
        raise ParseError(
            f"Unexpected token {token.type.name} at {token.line}:{token.column}"
        )
    
    def parse_array_literal(self) -> ArrayLiteral:
        """Parse array literal: [1, 2, 3]"""
        bracket_token = self.advance()  # Skip [
        
        elements = []
        while not self.match(TokenType.RBRACKET):
            elements.append(self.parse_expression())
            if self.match(TokenType.COMMA):
                self.advance()
        
        self.expect(TokenType.RBRACKET)
        
        return ArrayLiteral(
            elements=elements,
            line=bracket_token.line,
            column=bracket_token.column
        )
