from lang_yacc import parser
from lang_lex import lexer
from analysis import analyze
import qbepy
import subprocess
import os

il = """
function w $add(w %a, w %b) {              # Define a function add
@start
	%c =w add %a, %b                   # Adds the 2 arguments
	ret %c                             # Return the result
}

# Define the string constant.
data $fmt = { b "hello world: %d", b 0 }

export function w $main() {                # Main function
@start
	%r =w call $add(w 1, w 1)          # Call add(1, 1)
	# call $printf(l $fmt, ..., w %r)    # Show the result
	ret %r
}
"""


code = '''
main fn() {
    val: = 1
    val = 10
    val2 UInt = 2 + 100
    val3: = val + val2

    // doIf: = true


    // if doIf {
        // val = 20
    // } else {
        // val = 30
    // }

    // return val3

    // ret val3
}
'''

il = '''
# Define the string constant.
export function w $main() {
@start
    %val_StackPtr =l alloc8 8
    %val2_StackPtr =l alloc8 8
    %val3_StackPtr =l alloc8 8

    # val: = 10
    storel 1, %val_StackPtr

    # val = 10
    storel 10, %val_StackPtr

    # val2 UInt = 2 + 100
    %anon1 =l add 2, 100
    storel %anon1, %val2_StackPtr

    # val3: = val + val2
    %anon2 =l loadl %val_StackPtr
    %anon3 =l loadl %val2_StackPtr
    %anon4 =l add %anon2, %anon3
    storel %anon4, %val3_StackPtr

    # return val3
    %anon5 =l loadl %val3_StackPtr
    ret %anon5
}
'''

TARGET = 'amd64_sysv'
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

ast = parser.parse(code)

if ast == None:
    raise Exception("Could not build syntax tree.")

analyze(ast)


# Compile to assembly
try:
    asm = qbepy.compile_il(il, target = TARGET)
    print(asm)
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

# Run assembler and linker
result = subprocess.run(['clang', 'target/main.s', '-o', output_file_path], capture_output=True, text=True)

if result.returncode == 0:
    print('Successfully outputted executable to {}'.format(output_file_path))
else:
    print('Error:\n', result.stderr)