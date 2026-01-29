#!/usr/bin/env python3
"""
WitcherScript Command-Line Interface
Usage: witcher [file.witcher]
- witcher                    : Start interactive mode
- witcher program.witcher    : Run a .witcher file
"""

import sys
import os

# Add current directory to path to import witcher_interpreter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from witcher_interpreter import run_witcher_script

def interactive_mode():
    """Start interactive REPL"""
    print("=== WitcherScript Interpreter ===")
    print("Type your Witcher code. Type 'quit' to exit.")
    print()

    lines = []
    while True:
        try:
            line = input("witcher> " if not lines else "       > ")
            if line.lower() == "quit":
                break

            lines.append(line)
            source = '\n'.join(lines)

            try:
                from witcher_interpreter import Lexer, Parser, Interpreter
                lexer = Lexer(source)
                tokens = lexer.tokenize()
                parser = Parser(tokens)
                ast = parser.parse()
                interpreter = Interpreter()
                interpreter.interpret(ast)
                lines = []  # Reset after successful execution
            except SyntaxError:
                # Continue reading for incomplete input
                continue
            except Exception as e:
                print(f"Error: {e}")
                lines = []

        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye, Witcher!")
            break

def run_file(file_path):
    """Run a .witcher file"""
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        sys.exit(1)

    if not file_path.endswith('.witcher'):
        print(f"Warning: File doesn't have .witcher extension: {file_path}", file=sys.stderr)

    try:
        with open(file_path, 'r') as f:
            source = f.read()
        run_witcher_script(source)
    except FileNotFoundError:
        print(f"Error: Cannot read file: {file_path}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    """Main entry point for WitcherScript CLI"""
    if len(sys.argv) < 2:
        # No arguments: interactive mode
        interactive_mode()
    else:
        # With arguments: run file
        run_file(sys.argv[1])

if __name__ == "__main__":
    main()
