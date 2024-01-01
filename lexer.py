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
    # NEW = auto()
    CREATE = auto()
    READ = auto()
    WRITE = auto()
    EXPORT = auto()
    DUMP = auto()
    LIST = auto()
    SEARCH = auto()
    PRINT = auto()
    COUNT = auto()
    RENAME = auto()
    DELETE = auto()
    ADD = auto()
    EDIT = auto()
    COPY = auto()
    # data
    UID = auto()
    NAME = auto()
    FILE = auto()
    VALUE = auto()
    STRING = auto()
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
    SW_FIELD = auto()
    SW_FIELD_VALUE = auto()
    SW_FIELD_DELETE = auto()
    SW_TAG = auto()
    SW_NOTE = auto()
    SW_MULTILINE_NOTE = auto()  # multiline note
    # error
    INVALID = auto()


# Lexer DFA states
class LexState(Enum):
    START = auto()
    WORD = auto()
    STRING = auto()


# Token classes
LEX_ACTIONS = [Tid.DATABASE, Tid.ITEM, Tid.FIELD, Tid.TAG]

LEX_DATABASE = [Tid.CREATE, Tid.READ, Tid.WRITE, Tid.EXPORT, Tid.DUMP, Tid.REPORT]
LEX_ITEM = [Tid.LIST, Tid.COUNT, Tid.PRINT, Tid.SEARCH, Tid.ADD, Tid.DELETE, Tid.COPY, Tid.EDIT]
LEX_TAG = [Tid.LIST, Tid.COUNT, Tid.SEARCH, Tid.ADD, Tid.DELETE, Tid.RENAME]
LEX_FIELD = [Tid.LIST, Tid.COUNT, Tid.SEARCH, Tid.ADD, Tid.DELETE, Tid.RENAME]

LEX_SUBCOMMANDS = [Tid.LIST, Tid.COUNT, Tid.SEARCH,
                   Tid.PRINT, Tid.DUMP,
                   Tid.RENAME, Tid.DELETE,
                   Tid.CREATE, Tid.COPY, Tid.ADD, Tid.EDIT]

LEX_MISC = [Tid.TRACE]

LEX_STRINGS = [Tid.NAME, Tid.STRING]
LEX_VALUES = [Tid.VALUE, Tid.NAME, Tid.FILE, Tid.STRING]

# Regular expressions
LONG_DATE_PATTERN = r'^\d\d/\d\d/\d\d\d\d'
SHORT_DATE_PATTERN = r'^\d\d/\d\d/\d\d'
MONTH_YEAR_PATTERN = r'^\d\d/\d\d'
FILE_PATTERN = r'^[a-z0-9]+\.[a-z0-9]+'
NAME_PATTERN = r'^[a-zA-Z_][a-zA-Z_0-9]*'
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
        pass

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
            'read': Tid.READ, 'write': Tid.WRITE, 'export': Tid.EXPORT,
            'print': Tid.PRINT, 'dump': Tid.DUMP,
            'list': Tid.LIST, 'count': Tid.COUNT, 'search': Tid.SEARCH,
            'create': Tid.CREATE, 'copy': Tid.COPY, 'add': Tid.ADD, 'edit': Tid.EDIT,
            'rename': Tid.RENAME, 'delete': Tid.DELETE,
            'report': Tid.REPORT, 'trace': Tid.TRACE
        }
        self.switches = {
            '-s': Tid.SW_SENSITIVE,
            '-n': Tid.SW_NAME,
            '-t': Tid.SW_TAG,
            '-f': Tid.SW_FIELD,
            '-fn': Tid.SW_FIELD,
            '-fd': Tid.SW_FIELD_DELETE,
            '-fv': Tid.SW_FIELD_VALUE,
            '-note': Tid.SW_NOTE,
            '-text': Tid.SW_MULTILINE_NOTE
        }
        # The formats are handled in a separate dictionary to keep them separate from the other keywords
        self.formats = {
            'json': Tid.FMT_JSON,
            'sql': Tid.FMT_SQL,
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

    def token(self, pattern: str) -> Token:
        """
        Check for matching patterns and return token code and data.
        Keywords are always checked first.
        The order patterns are checked matters.
        :param pattern: pattern to chek
        :return: Token
        """
        if pattern in self.keywords:
            t = Token(self.keywords[pattern], pattern)
        elif pattern in self.switches:
            t = Token(self.switches[pattern], True)
        elif pattern in self.formats:
            t = Token(self.formats[pattern], pattern)
        elif re.search(LONG_DATE_PATTERN, pattern) \
                or re.search(SHORT_DATE_PATTERN, pattern) \
                or re.search(MONTH_YEAR_PATTERN, pattern):
            t = Token(Tid.VALUE, pattern)
        elif re.search(FLOAT_PATTERN, pattern):
            t = Token(Tid.VALUE, float(pattern))
        elif re.search(INT_PATTERN, pattern):
            t = Token(Tid.VALUE, int(pattern))
        elif re.search(FILE_PATTERN, pattern):
            t = Token(Tid.FILE, pattern)
        elif re.search(NAME_PATTERN, pattern):
            t = Token(Tid.NAME, pattern)
        else:
            t = Token(Tid.INVALID, pattern)
        return t

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
    lx.input('item name "this is a string" security_1 list 20/10/2022 07/24 3.4 7 -s -n -t -fn -fv -note')
    while True:
        tok = lx.next_token()
        print(tok)
        if tok.tid in [Tid.EOS, Tid.INVALID]:
            break
