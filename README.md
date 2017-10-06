.: Parth :.
===========

My own little parser library because I keep ending up writing parsers...

This is a place for me to explore different lexing and parsing techniques.


### Contents
- `simplex` A very basic lexer: create an instance, register tags
```python
l = Lexer()

@l.tag('DIGIT', r'\d')
def make_digit(s):
    return int(s)


@l.tag('DASH', r'-')
def make_dash(s):
    return s


for t in l.lex('12-345-997'):
    print(t)


>>> token(tag='DIGIT', value=1)
    token(tag='DIGIT', value=2)
    token(tag='DASH', value='-')
    token(tag='DIGIT', value=3)
    token(tag='DIGIT', value=4)
    token(tag='DIGIT', value=5)
    token(tag='DASH', value='-')
    token(tag='DIGIT', value=9)
    token(tag='DIGIT', value=9)
    token(tag='DIGIT', value=7)
```
