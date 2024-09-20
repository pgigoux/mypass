from lexer import Lexer, Token, Tid, UNTERMINATED_STRING


def test_keywords():
    lx = Lexer()

    assert lx.token('db') == Token(Tid.DATABASE, 'db')
    assert lx.token('item') == Token(Tid.ITEM, 'item')
    assert lx.token('field') == Token(Tid.FIELD, 'field')
    assert lx.token('tag') == Token(Tid.TAG, 'tag')

    assert lx.token('read') == Token(Tid.READ, 'read')
    assert lx.token('write') == Token(Tid.WRITE, 'write')
    assert lx.token('export') == Token(Tid.EXPORT, 'export')

    assert lx.token('use') == Token(Tid.USE, 'use')
    assert lx.token('list') == Token(Tid.LIST, 'list')
    assert lx.token('search') == Token(Tid.SEARCH, 'search')
    assert lx.token('print') == Token(Tid.PRINT, 'print')
    assert lx.token('count') == Token(Tid.COUNT, 'count')
    assert lx.token('rename') == Token(Tid.RENAME, 'rename')
    assert lx.token('delete') == Token(Tid.DELETE, 'delete')
    assert lx.token('create') == Token(Tid.CREATE, 'create')
    assert lx.token('add') == Token(Tid.ADD, 'add')
    assert lx.token('update') == Token(Tid.UPDATE, 'update')

    assert lx.token('dump') == Token(Tid.DUMP, 'dump')
    assert lx.token('report') == Token(Tid.REPORT, 'report')
    assert lx.token('trace') == Token(Tid.TRACE, 'trace')

    assert lx.token(':') == Token(Tid.SC_ITEM_PRINT, ':')
    assert lx.token('/') == Token(Tid.SC_ITEM_SEARCH, '/')


def test_switches():
    lx = Lexer()
    assert lx.token('-s') == Token(Tid.SW_SENSITIVE, True)
    assert lx.token('-n') == Token(Tid.SW_NAME, True)
    assert lx.token('-t') == Token(Tid.SW_TAG, True)
    assert lx.token('-fn') == Token(Tid.SW_FIELD_NAME, True)
    assert lx.token('-fv') == Token(Tid.SW_FIELD_VALUE, True)
    assert lx.token('-note') == Token(Tid.SW_NOTE, True)


def test_expressions():
    lx = Lexer()
    assert lx.token('100') == Token(Tid.INT, 100)
    assert lx.token('3.15') == Token(Tid.FLOAT, 3.15)
    assert lx.token('10/10/2020') == Token(Tid.DATE, '10/10/2020')
    assert lx.token('10/11') == Token(Tid.DATE, '10/11')
    assert lx.token('file.txt') == Token(Tid.FILE, 'file.txt')
    assert lx.token('/home/file.txt') == Token(Tid.FILE, '/home/file.txt')
    assert lx.token('/home/file.txt') == Token(Tid.FILE, '/home/file.txt')
    assert lx.token('data/file.txt') == Token(Tid.FILE, 'data/file.txt')
    assert lx.token('word') == Token(Tid.NAME, 'word')
    assert lx.token('o123') == Token(Tid.NAME, 'o123')
    assert lx.token('123-456-789') == Token(Tid.NAME, '123-456-789')
    assert lx.token('1.234.567-8') == Token(Tid.NAME, '1.234.567-8')


def test_strings():
    lx = Lexer()

    lx.input('"this is a string"')
    assert lx.next_token() == Token(Tid.STRING, 'this is a string')

    lx.input("'this is another string'")
    assert lx.next_token() == Token(Tid.STRING, 'this is another string')

    lx.input("'this is an unterminated string")
    token = lx.next_token()
    assert token.tid == Tid.INVALID and token.value.find(UNTERMINATED_STRING) == 0

    lx.input("'this is another unterminated string")
    assert token.tid == Tid.INVALID and token.value.find(UNTERMINATED_STRING) == 0


def test_next():
    lx = Lexer()

    lx.input('item search name 8 "one string" joe')
    assert lx.next_token() == Token(Tid.ITEM, 'item')
    assert lx.next_token() == Token(Tid.SEARCH, 'search')
    assert lx.next_token() == Token(Tid.NAME, 'name')
    assert lx.next_token() == Token(Tid.INT, 8)
    assert lx.next_token() == Token(Tid.STRING, 'one string')
    assert lx.next_token() == Token(Tid.NAME, 'joe')
    assert lx.next_token() == Token(Tid.EOS, '')

    lx.input('field list "some unterminated string 8')
    assert lx.next_token() == Token(Tid.FIELD, 'field')
    assert lx.next_token() == Token(Tid.LIST, 'list')
    token = lx.next_token()
    assert token.tid == Tid.INVALID and token.value.find(UNTERMINATED_STRING) == 0


if __name__ == '__main__':
    test_keywords()
    test_expressions()
    test_switches()
    test_strings()
    test_next()
