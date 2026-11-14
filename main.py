from lang_yacc import parser
from lang_lex import lexer
from analysis import analyze
import qbepy
import subprocess

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

# compile to assembly
asm = qbepy.compile_il(il, target = 'amd64_win')
with open('target/main.s', 'w', encoding='utf-8') as f:
    print(asm, file=f)

result = subprocess.run(['clang', 'target/main.s', '-o', 'target/main.exe'], capture_output=True, text=True)
if result.returncode == 0:
    print('successfully outputted main.exe')
else:
    print('Error:\n', result.stderr)

exit()


code = '''
main fn() {
    val: = 10
    val2 UInt = 2 + 100
    val3: = val + val2

    // doIf: = true


    // if doIf {
        // val = 20
    // } else {
        // val = 30
    // }

    ret val
}
'''

target_qbe = '''
# Define the string constant.
data $str = { b "hello world", b 0 }

export function w $main() {
@start
    %val =l 10
    %val2 =l add 2, 100
    %val3 =l add %val1, %val2

    %doIf =w 1

    jnz %doIf, 
@if_true_0
    %val =l 20
    jmp @if_end_0
@if_false_0
    %val =l 30

@if_end_0


    %r =w call $puts(l $str)
    ret 0
}
'''

lexer.input(code)
tokens = []
while True:
    token = lexer.token()
    print("Token: ", token)
    if token != None:
        tokens.append(token)
    else:
        break

# for token in tokens:
    # print(token)

ast = parser.parse(code)

if ast == None:
    raise Exception("Could not build syntax tree.")
print(ast)
analyze(ast)



