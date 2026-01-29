import argparse
import sys
import unittest
from .core import CKRLexer, CKRParser, CKREvaluator, CKRRuntimeError, START_MARKER, END_MARKER

# --- Testing Suite (Moved from generic main) ---
class CKRTests(unittest.TestCase):
    def setUp(self):
        self.lexer = CKRLexer()
        self.parser = CKRParser()
        self.evaluator = CKREvaluator()

    def run_code(self, raw_code):
        instructions, labels = self.parser.parse(self.lexer.tokenize(raw_code))
        self.evaluator.run(instructions, labels)

    def test_basic_math(self):
        code = """
        흑백요리사2 히든백수저 최강록
        나야 A
        A 조려
        A 조려
        백수저 최강록 우승
        """
        self.run_code(code)
        self.assertEqual(self.evaluator.variables['A'], 2)

    def test_immutability(self):
        code = """
        흑백요리사2 히든백수저 최강록
        부들부들 조려
        백수저 최강록 우승
        """
        with self.assertRaises(CKRRuntimeError):
            self.run_code(code)

    def test_comments(self):
        code = """
        흑백요리사2 히든백수저 최강록
        "이것은 주석입니다 나야 A"
        나야 B
        '이것 도 주석'
        백수저 최강록 우승
        """
        self.run_code(code)
        self.assertNotIn('A', self.evaluator.variables)
        self.assertIn('B', self.evaluator.variables)

def main():
    parser = argparse.ArgumentParser(description="ChoiKangRok Esolang Interpreter")
    parser.add_argument("file", nargs="?", help="Source file (.ckr) to execute")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug/tracing mode")
    parser.add_argument("--test", action="store_true", help="Run internal unit tests")
    
    args = parser.parse_args()

    if args.test:
        # Run unittests
        # Manually load tests from the CKRTests class to avoid discovery issues
        suite = unittest.TestLoader().loadTestsFromTestCase(CKRTests)
        unittest.TextTestRunner().run(suite)
        return

    lexer = CKRLexer()
    parser_ckr = CKRParser()
    evaluator = CKREvaluator(debug=args.debug)

    if args.file:
        # File Execution
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                raw_code = f.read()
            instructions, labels = parser_ckr.parse(lexer.tokenize(raw_code))
            evaluator.run(instructions, labels)
        except Exception as e:
            print(f"Error: {e}")
    else:
        # REPL Mode (Interactive)
        print("=== 최강록 인터프리터 (REPL) ===")
        print("Tip: '흑백요리사2 히든백수저 최강록'으로 시작하지 않아도 한 줄씩 테스트 가능합니다.")
        print("     exit() 또는 Ctrl+C로 종료.")
        
        while True:
            try:
                user_input = input(">>> ")
                if user_input.lower() in ["exit()", "quit"]: break
                
                # REPL Hack: Wrap input in markers to satisfy Lexer if needed
                if START_MARKER not in user_input:
                    wrapped_code = f"{START_MARKER}\n{user_input}\n{END_MARKER}"
                else:
                    wrapped_code = user_input
                
                instructions, labels = parser_ckr.parse(lexer.tokenize(wrapped_code))
                evaluator.run(instructions, labels) 
                
            except Exception as e:
                print(f"Error: {e}")
            except KeyboardInterrupt:
                print("\n종료합니다.")
                break
