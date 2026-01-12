"""
Command-line interface for ClearScript compiler.
"""

import sys
import argparse
from pathlib import Path
from .lexer import Lexer
from .parser import Parser
from .codegen import CodeGenerator


def compile_file(input_path: str, output_path: str = None, to_stdout: bool = False) -> bool:
    """
    Compile a ClearScript file to StateScript.
    
    Args:
        input_path: Path to the .cst input file
        output_path: Path to the .ss output file (optional)
        to_stdout: If True, print to stdout instead of file
    
    Returns:
        True if compilation succeeded, False otherwise
    """
    try:
        # Read input file
        with open(input_path, 'r', encoding='utf-8') as f:
            source = f.read()
        
        # Lexical analysis
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        
        # Parsing
        parser = Parser(tokens)
        ast = parser.parse()
        
        # Type check (unless disabled)
        if not args.no_typecheck:
            from .typechecker import TypeChecker
            checker = TypeChecker(ast)
            errors = checker.check()
            
            if errors:
                print(f"Type checking failed with {len(errors)} error(s):", file=sys.stderr)
                for error in errors:
                    print(f"  {error}", file=sys.stderr)
                return False
        
        # Code generation
        codegen = CodeGenerator(ast)
        output = codegen.generate()
        
        # Output
        if to_stdout:
            print(output)
        else:
            # Determine output path
            if output_path is None:
                input_file = Path(input_path)
                output_path = input_file.with_suffix('.ss')
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(output)
            
            print(f"Successfully compiled {input_path} -> {output_path}")
        
        return True
    
    except FileNotFoundError:
        print(f"Error: File not found: {input_path}", file=sys.stderr)
        return False
    
    except Exception as e:
        print(f"Compilation error: {e}", file=sys.stderr)
        return False


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description='ClearScript Compiler - Convert C-styled ClearScript to StateScript',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  clearscript compile input.cst                 # Compile to input.ss
  clearscript compile input.cst -o output.ss    # Compile to specific output
  clearscript compile input.cst --stdout        # Print to stdout
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Compile command
    compile_parser = subparsers.add_parser('compile', help='Compile ClearScript to StateScript')
    compile_parser.add_argument('input', help='Input ClearScript file (.cst)')
    compile_parser.add_argument('-o', '--output', help='Output StateScript file (.ss)')
    compile_parser.add_argument('--stdout', action='store_true', help='Print to stdout instead of file')
    compile_parser.add_argument('--no-typecheck', action='store_true', help='Disable type checking')
    
    # Version command
    version_parser = subparsers.add_parser('version', help='Show version information')
    
    args = parser.parse_args()
    
    # Handle commands
    if args.command == 'compile':
        success = compile_file(args.input, args.output, args.stdout)
        sys.exit(0 if success else 1)
    
    elif args.command == 'version':
        from . import __version__
        print(f"ClearScript v{__version__}")
        sys.exit(0)
    
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
