'''
A pratt parser with some built in parselets for common grammar elements
'''


# Built in grammar decorators for common grammar elements
def prefix(tag, precedence, func=None):
    '''
    A handler for a prefix operation. Creates a null handler for the
    given tag. The function will be passed the operand.
    '''
    if func is None:
        return lambda f: prefix(tag, precedence, f)

    func._is_prefix = True
    func._tag = tag
    func._precedence = precedence
    return func


def infix(tag, precedence, func=None):
    '''
    A handler for a left associative infix operation.
    Creates a left handler for the given tag which will be passed
    the left and right operands.
    '''
    if func is None:
        return lambda f: infix(tag, precedence, f)

    func._is_infix = True
    func._tag = tag
    func._precedence = precedence
    return func


def infix_r(tag, precedence, func=None):
    '''
    A handler for a right associative infix operation.
    Creates a left handler for the given tag which will be passed
    the left and right operands.
    '''
    if func is None:
        return lambda f: infix_r(tag, precedence, f)

    func._is_infix = True
    func._tag = tag
    func._precedence = precedence - 1
    return func


def postfix(tag, precedence, func=None):
    '''
    A handler for a postfix operation.
    Creates a left handler for the given tag which will be passed
    the left and right operands.
    '''
    if func is None:
        return lambda f: postfix(tag, precedence, f)

    func._is_postfix = True
    func._tag = tag
    func._precedence = precedence
    return func


def surrounding(start, end, precedence, func=None):
    '''
    A handler for expressions that surround others such as parens.

    The handler will be passed the expression between `start` and `end`.
    '''
    if func is None:
        return lambda f: surrounding(start, end, precedence, f)

    func._is_surrounding = True
    func._start = start
    func._end = end
    func._precedence = precedence
    return func


class Parselet:
    '''
    A parselet knows how to parse a given token in one (or both)
    of two ways:
       - `null` can be called by values and prefix operators. It doesn't
         care about tokens to the left.
       - `left` can be called when we care about tokens to the left such as
         infix, postfix and mixfix operators.
    '''
    def __init__(self, precedence, null, left):
        self.precedence = precedence
        self.null = null
        self.left = left

    def update(self, precedence=0, null=None, left=None):
        '''Update an existing Parselet with new methods or precedence'''
        self.precedence = max(self.precedence, precedence)

        if null is not None:
            if self.null is None:
                self.null = null
            else:
                raise RuntimeError('null handler already defined')

        if left is not None:
            if self.left is None:
                self.left = left
            else:
                raise RuntimeError('left handler already defined')


class Parser:
    '''
    A simple Pratt parser
    '''
    SYMBOLS = []
    LITERALS = []

    def __init__(self, lexer):
        self.lexer = lexer
        self.parselets = {}
        self.tokens = None
        self.lookahead = None

        # Register parselets tagged with the decorators
        for f in dir(self):
            f = getattr(self, f)
            if hasattr(f, '_is_prefix'):
                self._add_prefix(f._tag, f._precedence, f)
            elif hasattr(f, '_is_infix'):
                self._add_infix(f._tag, f._precedence, f)
            elif hasattr(f, '_is_postfix'):
                self._add_postfix(f._tag, f._precedence, f)
            elif hasattr(f, '_is_surrounding'):
                self._add_surrounding(f._start, f._end, f._precedence, f)

        for s in self.SYMBOLS:
            self._add_symbol(s)

        for l in self.LITERALS:
            self._add_literal(l)

    def _add_or_update_parselet(self, tag, precedence=0, null=None, left=None):
        '''Update and existing parselet or create it'''
        existing = self.parselets.get(tag)

        if existing:
            existing.update(precedence, null, left)
        else:
            self.parselets[tag] = Parselet(precedence, null, left)

    def _add_null_handler(self, tag, precedence, func):
        '''Add a function as the null handler for a given tag'''
        self._add_or_update_parselet(tag, precedence, null=func)

    def _add_left_handler(self, tag, precedence, func):
        '''Add a function as the left handler for a given tag'''
        self._add_or_update_parselet(tag, precedence, left=func)

    def _add_symbol(self, tag):
        '''Mark a tag for use in other grammar rules'''
        self._add_or_update_parselet(tag)

    def _add_prefix(self, tag, precedence, func):
        def null(token):
            operand = self._parse(precedence)
            return func(operand)
        self._add_null_handler(tag, precedence, null)

    def _add_infix(self, tag, precedence, func):
        def left(token, left):
            right = self._parse(precedence)
            return func(left, right)
        self._add_left_handler(tag, precedence, left)

    def _add_postfix(self, tag, precedence, func):
        def left(token):
            return func(token.value)
        self._add_left_handler(tag, precedence, left)

    def _add_surrounding(self, start, end, precedence, func):
        def null(token):
            body = self._parse()
            # Pull off the closing deliminator to get rid of it
            self._advance(end)
            return func(body)
        self._add_symbol(end)
        self._add_null_handler(start, precedence, null)

    def _add_literal(self, tag):
        '''
        Handle a literal value from the lexer that is no longer a token
        '''
        self._add_null_handler(tag, 0, lambda value: value)

    def parse(self, program):
        '''
        Parse a program
        '''
        self.tokens = self.lexer.lex(program)
        self.lookahead = next(self.tokens)
        self.input_remaining = True
        val = None

        while self.input_remaining:
            val = self._parse(left_value=val)

        return val

    def _advance(self, tag):
        '''
        If the next token has a tag of `tag` then return it
        otherwise return None.
        '''
        if self.lookahead.tag == tag:
            advanced = self.lookahead
            try:
                self.lookahead = next(self.tokens)
            except StopIteration:
                # This was the last token so stop parsing
                self.input_remaining = False
            return advanced
        else:
            return None

    def _parse(self, max_bind=0, left_value=None):
        '''
        Parse and return an expression until a token with a
        binding >= `max_bind` is found.
        '''
        if left_value is None:
            early_return = False
            initial = self.lookahead

            try:
                self.lookahead = next(self.tokens)
            except StopIteration:
                early_return = True

            left_value = self._call_null(initial)

            if early_return:
                # This was the last token so there's nothing else to parse
                self.input_remaining = False
                return left_value

        try:
            while max_bind < self.parselets[self.lookahead.tag].precedence:
                left_token = self.lookahead
                self.lookahead = next(self.tokens)
                left_value = self._call_left(left_token, left_value)
        except StopIteration:
            self.input_remaining = False

        return left_value

    def _get_parselet(self, token):
        '''Get the parselet for a given token or raise an exception'''
        parselet = self.parselets.get(token.tag)
        if parselet is None:
            raise SyntaxError('Unexpected token: {!r}'.format(token.text))

        return parselet

    def _call_null(self, token):
        '''
        Find the correct parselet for this token type and call its
        null handler.

        Raises a SyntaxError if there is no null handler for `token`.
        '''
        func = self._get_parselet(token).null
        if func is None:
            raise SyntaxError('Unexpected token: {!r}'.format(token.text))

        return func(token.value)

    def _call_left(self, token, left):
        '''
        Find the correct parselet for this token type and call its
        null handler.

        Raises a SyntaxError if there is no left handler for `token`.
        '''
        func = self._get_parselet(token).left
        if func is None:
            raise SyntaxError('Unexpected token: {!r}'.format(token.text))

        return func(token.value, left)
