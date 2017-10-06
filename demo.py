from simplex import Lexer
from parsnip import Parser

l = Lexer()


@l.tag('INT', r'-?\d+')
def mkint(s):
    return int(s)


l.symbol('ADD', r'\+')
l.symbol('SUB', r'-')
l.symbol('MUL', r'\*')
l.symbol('DIV', r'/')
l.symbol('LPAREN', r'\(')
l.symbol('RPAREN', r'\)')
l.ignore(r'\s+')
l.ignore(r'\n')

p = Parser(l)
p.literal('INT')
p.symbol('ADD')
p.symbol('SUB')
p.symbol('MUL')
p.symbol('DIV')


@p.prefix('SUB', 10)
def negate(val):
    return -val


@p.infix('ADD', 1)
def add(l, r):
    return l + r


@p.infix('SUB', 1)
def sub(l, r):
    return l - r


@p.infix('MUL', 5)
def mul(l, r):
    return l * r


@p.infix('DIV', 5)
def div(l, r):
    return l / r


@p.surrounding('LPAREN', 'RPAREN', 0)
def parens(expr):
    return expr


text = '(12 + 6) / (4 - 9)'
print('Parsing: {}'.format(text))
print(p.parse(text))
