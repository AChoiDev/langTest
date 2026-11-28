from lang_yacc import parser
from lang_lex import lexer
from analysis import analyze, print_ast
import qbepy
import subprocess
import os
from emit import emit_file

code = None
with open("main.rs", "r", encoding="utf-8") as f:
    code = f.read()
    f.flush()

TARGET = 'amd64_win'
OUTPUT_FILE = 'main'
if TARGET.endswith('_win'):
    OUTPUT_FILE = 'main.exe'
output_file_path = 'target/{}'.format(OUTPUT_FILE)


# Obtain token list
lexer.input(code)
tokens = []
while True:
    token = lexer.token()
    # print("Token: ", token)
    if token != None:
        tokens.append(token)
    else:
        break

print('starting ast parse')
ast = parser.parse(code, debug=True)
print_ast(ast, 0)

if ast == None:
    raise Exception("Could not build syntax tree.")

print('starting ast analysis')
analyze(ast)
print('AST analysis succeeded')
print_ast(ast, 0)
il = emit_file(ast)
print('QBE IL Emitted')

with open('target/main.qbe', 'w', encoding='utf-8') as f:
    print(il, file=f)
    f.flush()

# Compile to assembly
try:
    asm = qbepy.compile_il(il, target = TARGET) # type: ignore (target)
except Exception as e:
    print("Error while using QBE to compile IR.")
    print(e)
    print('Exiting application')
    exit()

# Write assembly to file
if not os.path.exists('target'):
    os.makedirs('target')

with open('target/main.s', 'w', encoding='utf-8') as f:
    print(asm, file=f)
    f.flush()

# Run assembler and linker
result = subprocess.run(['clang', 'target/main.s', '-o', output_file_path], capture_output=True, text=True)

if result.returncode == 0:
    print('Successfully outputted executable to {}'.format(output_file_path))
else:
    print('Error:\n', result.stderr)