'''
Simple regex based lexing.
'''
import re
from collections import namedtuple


Tag = namedtuple('tag', 'tag regex')
Token = namedtuple('token', 'tag value text')


def lex_error(s):
    raise SyntaxError("Unable to parse input: {}".format(s))


def tag(_tag, regex, func=None):
    '''
    Add a new tag to match and a function to generate a datatype from.
    '''
    if func is None:
        return lambda f: tag(_tag, regex, f)

    # We're not modifying the function, we're just tagging it
    # for the lexer so return what was passed in
    func._is_tag = True
    func._tag = _tag
    func._regex = regex
    return func


class Lexer:
    IGNORE = []
    SYMBOLS = []

    def __init__(self):
        # In python 3.6 we could just rely on ordered dicts...!
        self.tag_map = {'LEX_ERROR': lex_error}
        self.tags = []
        self.regex = None
        self._ignore_count = 0

        for f in dir(self):
            f = getattr(self, f)
            if hasattr(f, '_is_tag'):
                self._add_tag(f._tag, f._regex, f)

        for i in self.IGNORE:
            self.ignore(i)

        for s in self.SYMBOLS:
            self.symbol(s[0], s[1])

        self._build()

    def ignore(self, regex):
        self.tags.append(Tag('IGNORE{}'.format(self._ignore_count), regex))
        self._ignore_count += 1

    def symbol(self, tag, regex):
        '''
        Add a raw symbol
        '''
        self.tag_map[tag] = lambda s: s
        self.tags.append(Tag(tag, regex))

    def _add_tag(self, tag, regex, func):
        '''
        Add a new tag to match and a function to generate a datatype from.
        '''
        self.tag_map[tag] = func
        self.tags.append(Tag(tag, regex))

    def _build(self):
        '''
        Build the lexer master regex
        '''
        # Add a catch-all tag to the end of our tags so that if we fail to
        # match any part of the input we raise a error
        self.tags.append(Tag('LEX_ERROR', '.'))
        tags = '|'.join('(?P<{}>{})'.format(t.tag, t.regex) for t in self.tags)
        self.regex = re.compile(tags)

    def lex(self, string):
        '''
        Tokenise an input string
        '''
        if self.regex is None:
            self._build()

        for match in re.finditer(self.regex, string):
            lex_tag = match.lastgroup

            if lex_tag.startswith('IGNORE'):
                continue

            # Take the selected version if we have it
            group = [g for g in match.groups() if g is not None]
            match_text = group[1] if len(group) == 2 else match.group(lex_tag)
            yield Token(lex_tag, self.tag_map[lex_tag](match_text), match_text)
