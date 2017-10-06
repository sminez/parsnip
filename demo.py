from simplex import Lexer, tag
from parsnip import Parser, infix, prefix, surrounding


class CalcLex(Lexer):
    IGNORE = ['\s+', '\n']
    SYMBOLS = [('ADD', r'\+'), ('SUB', r'-'), ('MUL', r'\*'),
               ('DIV', r'/'), ('LPAREN', r'\('), ('RPAREN', r'\)')]

    @tag('INT', r'-?\d+')
    def mkint(self, s):
        return int(s)


class CalcParse(Parser):
    SYMBOLS = []
    LITERALS = ['INT']

    @prefix('SUB', 10)
    def negate(self, val):
        return -val

    @infix('ADD', 1)
    def add(self, l, r):
        return l + r

    @infix('SUB', 1)
    def sub(self, l, r):
        return l - r

    @infix('MUL', 5)
    def mul(self, l, r):
        return l * r

    @infix('DIV', 5)
    def div(self, l, r):
        return l / r

    @surrounding('LPAREN', 'RPAREN', 0)
    def parens(self, expr):
        return expr


l = CalcLex()
p = CalcParse(l)
text = '(12 + 6) / (4 - 9)'

print('Parsing: {}'.format(text))
print(p.parse(text))
