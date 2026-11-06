from lang_yacc import parser
from lang_lex import lexer
from analysis import analyze


code = '''
main fn() {
    val: = 10
    val2 UInt = 2 + 100
    val3: = val + val2
    // add UInt = val + 1

    // 3498
}
'''

lexer.input(code)
tokens = []
while True:
    token = lexer.token()
    if token != None:
        tokens.append(token)
    else:
        break

for token in tokens:
    print(token)

ast = parser.parse(code)

if ast == None:
    raise Exception("could not parse code")
print(ast)
analyze(ast)
