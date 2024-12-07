import re
from enum import Enum, auto


# Token identifiers
class Tid(Enum):
    # commands
    DATABASE = auto()
    ITEM = auto()
    TAG = auto()
    FIELD = auto()
    # subcommands
    CREATE = auto()
    READ = auto()
    WRITE = auto()
    EXPORT = auto()
    IMPORT = auto()
    DUMP = auto()
    LIST = auto()
    SEARCH = auto()
    PRINT = auto()
    COUNT = auto()
    RENAME = auto()
    DELETE = auto()
    ADD = auto()
    UPDATE = auto()
    COPY = auto()
    NOTE = auto()
    USE = auto()
    # data
    FILE = auto()
    DATE = auto()
    STRING = auto()
    INT = auto()
    FLOAT = auto()
    NAME = auto()  # anything string with no whitespaces
    # misc
    REPORT = auto()
    TRACE = auto()
    EOS = auto()
    # formats
    FMT_JSON = auto()
    FMT_SQL = auto()
    # switches
    SW_SENSITIVE = auto()
    SW_NAME = auto()
    SW_FIELD_NAME = auto()
    SW_FIELD_VALUE = auto()
    SW_TAG = auto()
    SW_NOTE = auto()
    # shortcuts
    SC_DB_READ = auto()
    SC_ITEM_PRINT = auto()
    SC_ITEM_SEARCH = auto()
    # error
    INVALID = auto()


# Lexer DFA states
class LexState(Enum):
    START = auto()
    WORD = auto()
    STRING = auto()


# Token classes
LEX_ACTIONS = [Tid.DATABASE, Tid.ITEM, Tid.FIELD, Tid.TAG]
LEX_MISC = [Tid.TRACE]
LEX_STRING = [Tid.NAME, Tid.STRING]
LEX_NUMBER = [Tid.INT, Tid.FLOAT]
LEX_VALUE = [Tid.INT, Tid.FLOAT, Tid.NAME, Tid.FILE, Tid.STRING]
LEX_SHORTCUTS = [Tid.SC_DB_READ, Tid.SC_ITEM_PRINT, Tid.SC_ITEM_SEARCH]

# Regular expressions
LONG_DATE_PATTERN = r'^\d\d/\d\d/\d\d\d\d'
SHORT_DATE_PATTERN = r'^\d\d/\d\d/\d\d'
MONTH_YEAR_PATTERN = r'^\d\d/\d\d'
FILE_PATTERN = r'^(\./)?[\w\-/]+\.[\w]+'
NAME_PATTERN = r'^\S+'
INT_PATTERN = r'^\d+'
FLOAT_PATTERN = r'^\d*\.\d+'

# Valid string delimiters
STRING_DELIMITERS = ['\'', '"']

# Unterminated string error message
UNTERMINATED_STRING = 'unterminated'


class Token:
    """
    Tokens are objects that have an id and value
    """

    def __init__(self, tid: Tid, value: int | float | str):
        self._tid = tid
        self._value = value

    def __eq__(self, token):
        if isinstance(token, Token):
            return self.tid == token.tid and self.value == token.value
        return False

    def __str__(self):
        return f'({self._tid}, {self._value})'

    @property
    def tid(self):
        return self._tid

    @property
    def value(self):
        return self._value


class Lexer:

    def __init__(self):
        self.command = ''
        self.count = 0
        self.char_list = []
        self.state = LexState.START
        self.keywords = {
            'db': Tid.DATABASE, 'item': Tid.ITEM, 'tag': Tid.TAG, 'field': Tid.FIELD,
            'read': Tid.READ, 'write': Tid.WRITE, 'import': Tid.IMPORT, 'export': Tid.EXPORT,
            'print': Tid.PRINT, 'dump': Tid.DUMP,
            'use': Tid.USE, 'note': Tid.NOTE, 'list': Tid.LIST, 'count': Tid.COUNT, 'search': Tid.SEARCH,
            'create': Tid.CREATE, 'copy': Tid.COPY, 'add': Tid.ADD, 'update': Tid.UPDATE,
            'rename': Tid.RENAME, 'delete': Tid.DELETE,
            'report': Tid.REPORT, 'trace': Tid.TRACE
        }
        self.switches = {
            '-s': Tid.SW_SENSITIVE,
            '-n': Tid.SW_NAME,
            '-t': Tid.SW_TAG,
            '-fn': Tid.SW_FIELD_NAME,
            '-fv': Tid.SW_FIELD_VALUE,
            '-note': Tid.SW_NOTE,
        }
        self.formats = {
            'json': Tid.FMT_JSON,
            'sql': Tid.FMT_SQL,
        }
        self.shortcuts = {
            '@': Tid.SC_DB_READ,
            '/': Tid.SC_ITEM_SEARCH,
            ':': Tid.SC_ITEM_PRINT
        }

    def input(self, command: str):
        """
        :param command:
        :return:
        """
        # the trailing space is needed by the state machine to parse properly
        self.command = command.strip()
        self.char_list = list(self.command + ' ')
        self.state = LexState.START
        self.count = 0

    @staticmethod
    def _match(pattern: str, word: str) -> bool:
        """
        Check whether the input word matches a regular expression.
        Make sure the matching string is the same as the full word
        :param pattern: regular expression pattern
        :param word: input word
        :return: True if there is a match, False otherwise
        """
        m = re.search(pattern, word)
        return True if m is not None and len(m.group()) == len(word) else False

    def token(self, word: str) -> Token:
        """
        Check word for matching patterns and return token code and data.
        The different keywords are always checked first.
        The pattern checking order is important.
        :param word: word to check against patterns
        :return: Token
        """
        if word in self.shortcuts:
            return Token(self.shortcuts[word], word)
        if word in self.keywords:
            return Token(self.keywords[word], word)
        if word in self.switches:
            return Token(self.switches[word], True)
        if word in self.formats:
            return Token(self.formats[word], word)

        if self._match(LONG_DATE_PATTERN, word) \
                or re.search(SHORT_DATE_PATTERN, word) \
                or re.search(MONTH_YEAR_PATTERN, word):
            return Token(Tid.DATE, word)

        try:
            if self._match(FLOAT_PATTERN, word):
                return Token(Tid.FLOAT, float(word))
            if self._match(INT_PATTERN, word):
                return Token(Tid.INT, int(word))
        except ValueError:
            return Token(Tid.INVALID, word)

        if self._match(FILE_PATTERN, word):
            return Token(Tid.FILE, word)
        if self._match(NAME_PATTERN, word):
            return Token(Tid.NAME, word)

        return Token(Tid.INVALID, word)

    def next_token(self) -> Token:
        """
        Return the next token in the input stream
        :return: tuple containing the token and value
        """
        word = ''
        while self.count < len(self.char_list):
            c = self.char_list[self.count]
            self.count += 1
            assert isinstance(c, str)
            if self.state == LexState.START:
                if c.isspace():
                    pass
                elif c in self.shortcuts and self.count == 1:
                    return self.token(c)
                elif c in STRING_DELIMITERS:
                    self.state = LexState.STRING  # start of string
                    word = ''
                else:
                    word = c
                    self.state = LexState.WORD  # start of word
            elif self.state == LexState.WORD:
                if c.isspace():
                    self.state = LexState.START
                    return self.token(word)  # end of word
                else:
                    word += c
            elif self.state == LexState.STRING:
                if c in STRING_DELIMITERS:
                    self.state = LexState.START
                    return Token(Tid.STRING, word)  # end of string
                else:
                    word += c

        # Check for unterminated string
        if self.state == LexState.STRING:
            return Token(Tid.INVALID, f'{UNTERMINATED_STRING} [{word[0:10]}...]')
        else:
            return Token(Tid.EOS, '')


if __name__ == '__main__':
    lx = Lexer()
    lx.input(
        'item name "this is a string" security_1 list 20/10/2022 07/24'
        ' /home/test_1.txt 8.310.444-3 3.4 7 333-555-8888 -s -n -t -fn -fv -note')
    while True:
        tok = lx.next_token()
        print(tok)
        if tok.tid in [Tid.EOS, Tid.INVALID]:
            break
