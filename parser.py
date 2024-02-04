from db import DEFAULT_DATABASE_NAME
from command import CommandProcessor, FileFormat
from command import KEY_ID, KEY_NAME, KEY_TIMESTAMP, KEY_NOTE, KEY_TAGS, KEY_FIELDS
from lexer import Lexer, Token, Tid
from lexer import LEX_ACTIONS, LEX_DATABASE, LEX_MISC, LEX_VALUE, LEX_STRING
from utils import error, trace, confirm, trace_toggle, sensitive_mark, timestamp_to_string

# Error messages
ERROR_UNKNOWN_COMMAND = 'unknown command'
ERROR_UNKNOWN_SUBCOMMAND = 'unknown subcommand'
ERROR_BAD_FILENAME = 'bad file name'
ERROR_BAD_FORMAT = 'bad format, expected "json" or "sql"'


class Parser:
    """
    Recursive descent parser to process commands
    """

    def __init__(self):
        self.lexer = Lexer()
        self.cmd = ''
        self.default_item_id = None
        self.cp = CommandProcessor(confirm=confirm)

    def get_token(self) -> Token:
        """
        Get next token from the lexer
        :return: token id and value
        """
        token = self.lexer.next_token()
        trace('get_token', token)
        return token

    # -------------------------------------------------------------
    # Tag
    # -------------------------------------------------------------

    @staticmethod
    def _format_table_tag(tag_id: int, tag_name: str, tag_count: int) -> str:
        return f'{tag_id:2d} {tag_count:3d} {tag_name}'

    def tag_list(self):
        trace('tag_list')
        r = self.cp.tag_table_list()
        if r.is_ok and r.is_list:
            for t_id, t_name, t_count in r.value:
                # print(f'{t_id:2d} {t_count:3d} {t_name}')
                print(self._format_table_tag(t_id, t_name, t_count))
        else:
            print(r)

    def tag_count(self):
        trace('tag_count')
        r = self.cp.tag_table_count()
        if r.is_ok:
            print(r.value)
        else:
            print(r)

    def tag_search(self, tok: Token):
        trace('tag_search', tok)
        r = self.cp.tag_table_search(tok.value)
        if r.is_ok and r.is_list:
            for t_id, t_name, t_count in r.value:
                print(self._format_table_tag(t_id, t_name, t_count))
        else:
            print(r)

    def tag_add(self, tok: Token):
        trace('tag_add', tok)
        print(self.cp.tag_table_add(tok.value))

    def tag_rename(self, tok1: Token, tok2: Token):
        trace('tag_rename', tok1, tok2)
        print(self.cp.tag_table_rename(tok1.value, tok2.value))

    def tag_delete(self, tok: Token):
        trace('tag_delete', tok)
        print(self.cp.tag_table_delete(tok.value))

    def tag_command(self, token: Token):
        """
        tag_command : TAG subcommand
        :param token: subcommand token
        """
        trace('tag_command', token)
        if token.tid == Tid.LIST:
            # self.cp.tag_list()
            self.tag_list()
        elif token.tid == Tid.COUNT:
            # self.cp.tag_count()
            self.tag_count()
        elif token.tid in [Tid.SEARCH, Tid.DELETE]:
            tok = self.get_token()
            if tok.tid in LEX_STRING:
                if token.tid == Tid.SEARCH:
                    trace('tag search', tok)
                    self.tag_search(tok)
                else:
                    trace('tag delete', tok)
                    self.tag_delete(tok)
            else:
                error('bad/missing tag name', tok)
        elif token.tid == Tid.ADD:
            tok = self.get_token()
            if tok.tid in LEX_STRING:
                # self.cp.tag_add(tok.value)
                self.tag_add(tok)
        elif token.tid == Tid.RENAME:
            tok1 = self.get_token()
            tok2 = self.get_token()
            if tok1.tid in LEX_STRING and tok2.tid in LEX_STRING:
                # self.cp.tag_rename(tok1.value, tok2.value)
                self.tag_rename(tok1, tok2)
            else:
                error('bad tag name', tok1, tok2)
        else:
            error(ERROR_UNKNOWN_SUBCOMMAND, token)

    # -------------------------------------------------------------
    # Fields
    # -------------------------------------------------------------

    @staticmethod
    def _format_table_field(field_id: int, field_name: str, field_sensitive: bool, field_count: int) -> str:
        return f'{field_id:3d} {field_count:4d} {sensitive_mark(field_sensitive)} {field_name}'

    def field_list(self):
        trace('field_list')
        r = self.cp.field_table_list()
        if r.is_ok and r.is_list:
            for f_id, f_name, f_sensitive, f_count in r.value:
                print(self._format_table_field(f_id, f_name, f_sensitive, f_count))
        else:
            print(r)

    def field_count(self):
        trace('field_count')
        r = self.cp.field_table_count()
        if r.is_ok:
            print(r.value)
        else:
            print(r)

    def field_search(self, tok: Token):
        trace('field_search', tok)
        r = self.cp.field_table_search(tok.value)
        if r.is_ok and r.is_list:
            for f_id, f_name, f_sensitive, f_count in r.value:
                print(self._format_table_field(f_id, f_name, f_sensitive, f_count))
        else:
            print(r)

    def field_add(self, tok: Token, sensitive: bool):
        trace('field_add', tok)
        print(self.cp.field_table_add(tok.value, sensitive))

    def field_rename(self, tok1: Token, tok2: Token):
        trace('field_rename', tok1, tok2)
        print(self.cp.field_table_rename(tok1.value, tok2.value))

    def field_delete(self, tok: Token):
        trace('field_delete', tok)
        print(self.cp.field_table_delete(tok.value))

    def field_command(self, token: Token):
        """
        field_command : FIELD subcommand
        :param token: subcommand token
        """
        trace('field_command', token)
        if token.tid == Tid.LIST:
            self.field_list()
        elif token.tid == Tid.COUNT:
            self.field_count()
        elif token.tid in [Tid.SEARCH, Tid.DELETE]:
            tok = self.get_token()
            if tok.tid in LEX_STRING:
                if token.tid == Tid.SEARCH:
                    trace('field search', tok)
                    self.field_search(tok)
                else:
                    trace('field delete', tok)
                    self.field_delete(tok)
            else:
                error('bad/missing field name', tok)
        elif token.tid == Tid.ADD:
            tok = self.get_token()
            trace('field add', tok)
            if tok.tid in LEX_STRING:
                s_tok = self.get_token()
                sensitive = True if s_tok.tid == Tid.SW_SENSITIVE else False
                self.field_add(tok, sensitive)
        elif token.tid == Tid.RENAME:
            tok1 = self.get_token()
            tok2 = self.get_token()
            if tok1.tid in LEX_STRING and tok2.tid in LEX_STRING:
                self.field_rename(tok1, tok2)
            else:
                error('bad field name', tok1, tok2)
        else:
            error(ERROR_UNKNOWN_SUBCOMMAND, token)

    # -------------------------------------------------------------
    # Item
    # -------------------------------------------------------------

    @staticmethod
    def _format_item(item_id: int, item_name: str, item_timestamp: int) -> str:
        return f'{item_id:5d}  {timestamp_to_string(item_timestamp, date_only=True)}  {item_name}'

    def item_options(self, tag_flag=False) -> tuple[str, list, str]:
        """
        Get item add/edit options
        :return: tuple
        """
        item_name = ''
        tag_list = []
        note = ""
        # multiline_note = False
        while True:
            token = self.get_token()
            trace('-- token', token)
            if token.tid == Tid.SW_NAME:
                t1 = self.get_token()
                trace('found name', t1)
                if t1.tid in LEX_STRING:
                    item_name = t1.value
                else:
                    raise ValueError(f'bad item name {t1}')

            elif token.tid == Tid.SW_TAG:
                if tag_flag:
                    t1 = self.get_token()
                    trace('found tag', t1)
                    if t1.tid == Tid.NAME:
                        tag_list.append(t1.value)
                    else:
                        raise ValueError(f'bad tag {t1}')
                else:
                    raise ValueError(f'option not allowed', token)

            elif token.tid == Tid.SW_NOTE:
                t1 = self.get_token()
                trace('found note', t1)
                if t1.tid in LEX_VALUE:
                    note = str(t1.value)
                else:
                    raise ValueError(f'bad note {t1}')

            # elif token.tid == Tid.SW_MULTILINE_NOTE:
            # TODO
            #     trace('found note text')
            #     multiline_note = True

            elif token.tid == Tid.EOS:
                trace('eos')
                break

            else:
                raise ValueError(f'unknown item option {token}')

        return item_name, tag_list, note

    def item_list(self):
        trace('item_list')
        r = self.cp.item_list()
        if r.is_ok and r.is_list:
            for i_id, i_name, i_timestamp, _ in r.value:
                print(self._format_item(i_id, i_name, i_timestamp))
        else:
            print(r)

    def item_count(self):
        trace('item_count')
        r = self.cp.item_list()
        if r.is_ok:
            print(self.cp.item_count())
        else:
            print(r)

    def item_search(self, token: Token):
        """
        item_search_command: ITEM SEARCH NAME search_option_list
        :return:
        """
        trace('item_search_command', token)
        pattern = token.value
        # Process flags
        name_flag, tag_flag, field_name_flag, field_value_flag, note_flag = (False, False, False, False, False)
        while True:
            tok = self.get_token()
            if tok.tid == Tid.EOS:
                break
            elif tok.tid == Tid.SW_NAME:
                name_flag = True
            elif tok.tid == Tid.SW_TAG:
                tag_flag = True
            elif tok.tid == Tid.SW_FIELD:
                field_name_flag = True
            elif tok.tid == Tid.SW_FIELD_VALUE:
                field_value_flag = True
            elif tok.tid == Tid.SW_NOTE:
                note_flag = True

        # Enable search by item name if no flags were specified
        if not any((name_flag, tag_flag, field_name_flag, field_value_flag, note_flag)):
            name_flag = True

        trace('to search', tok.value, name_flag, tag_flag, field_name_flag, field_value_flag, note_flag)
        r = self.cp.item_search(pattern, name_flag, tag_flag, field_name_flag, field_value_flag, note_flag)
        if r.is_ok and r.is_list:
            for i_id, i_name, i_timestamp in r.value:
                print(self._format_item(i_id, i_name, i_timestamp))
        else:
            print(r)

    def item_add(self):
        """
        Add new item
        """
        trace('item_add')
        item_name, tag_list, note = self.item_options(tag_flag=True)
        trace('item_add', item_name, tag_list, note)
        print(self.cp.item_add(item_name, tag_list, note))

    def item_delete(self, token: Token):
        """
        Delete existing item
        :param token: item id token
        """
        trace('item_delete', token)
        print(self.cp.item_delete(token.value))

    def item_copy(self, token: Token):
        """
        Duplicate item
        :param token: item id token
        """
        trace('item_copy', token)
        print(self.cp.item_copy(token.value))

    def item_update(self, token: Token):
        """
        Edit existing item
        :param token: item id token
        """
        trace('item_update', token)
        item_name, _, note = self.item_options()
        trace('item_update', item_name, note)
        print(self.cp.item_update(token.value, item_name, note))

    def item_tag_command(self, token: Token):
        """
        Add tag to item
        :param token: subcommand token
        """
        trace('item_tag_command', token)
        tok1 = self.get_token()
        if tok1.tid == Tid.INT:
            tok2 = self.get_token()
            if tok2.tid == Tid.NAME:
                if token.tid == Tid.ADD:
                    trace('tag add', tok1, tok2)
                    print(self.cp.tag_add(tok1.value, tok2.value))
                elif token.tid == Tid.DELETE:
                    trace('tag delete', tok1, tok2)
                    print(self.cp.tag_delete(tok1.value, tok2.value))
                else:
                    error('Invalid tag subcommand', token)
            else:
                error('tag name expected', tok2)
        else:
            error('item id expected', tok1)

    def item_field_command(self, token: Token):
        """
        TODO
        :param token:
        :return:
        """
        trace('item_field_command', token)

    def item_print(self, token: Token):
        """
        item_print_command: PRINT [SW_SENSITIVE]
        :param token: item token
        """
        tok = self.get_token()
        show_encrypted = True if tok.tid == Tid.SW_SENSITIVE else False
        r = self.cp.item_get(token.value)
        if r.is_ok and r.is_dict:
            d = r.value
            assert isinstance(d, dict)
            print(f'id:    {d[KEY_ID]}')
            print(f'name:  {d[KEY_NAME]}')
            print(f'date:  {timestamp_to_string(d[KEY_TIMESTAMP])}')
            print(f'tags:  {d[KEY_TAGS]}')
            print('fields:')
            for f_id, f_name, f_value, f_encrypted in d[KEY_FIELDS]:
                f_value = self.cp.decrypt_value(f_value) if f_encrypted and show_encrypted else f_value
                print(f'  {f_id:4d} {sensitive_mark(f_encrypted)} {f_name} {f_value}')
                del f_value
            print('note:')
            if len(d[KEY_NOTE]) > 0:
                print(f'{d[KEY_NOTE]}')
        else:
            print(r)

    def item_command(self, token: Token):
        """
        item_command : ITEM subcommand
        :param token: subcommand token
        """
        trace('item_command', token)
        if token.tid == Tid.LIST:
            self.item_list()
        elif token.tid in [Tid.USE, Tid.PRINT, Tid.DELETE, Tid.COPY, Tid.UPDATE]:
            tok = self.get_token()
            trace('item print, dump, delete, copy, tag, field', tok)
            if tok.tid == Tid.INT:
                if token.tid == Tid.USE:
                    self.default_item_id = tok.value
                elif token.tid == Tid.PRINT:
                    self.item_print(tok)
                elif token.tid == Tid.DELETE:
                    self.item_delete(tok)
                elif token.tid == Tid.COPY:
                    self.item_copy(tok)
                elif token.tid == Tid.UPDATE:
                    self.item_update(tok)
                else:
                    error('Unknown item subcommand', tok)
            else:
                error('item id expected', tok)
        elif token.tid == Tid.TAG:
            tok = self.get_token()
            trace('item tag', tok)
            if tok.tid in [Tid.ADD, Tid.DELETE, Tid.RENAME]:
                self.item_tag_command(tok)
            else:
                error('Invalid item tag subcommand', tok)
        elif token.tid == Tid.FIELD:
            tok = self.get_token()
            trace('item field', tok)
            if tok.tid in [Tid.ADD, Tid.DELETE, Tid.RENAME, Tid.UPDATE]:
                self.item_field_command(tok)
            else:
                error('Invalid item tag subcommand', tok)
        elif token.tid == Tid.COUNT:
            trace('item count', token)
            self.item_count()
        elif token.tid == Tid.SEARCH:
            tok = self.get_token()
            trace('item search', tok)
            if tok.tid in LEX_STRING:
                self.item_search(tok)
            else:
                error('pattern expected')
        elif token.tid == Tid.ADD:
            trace('item add', token)
            self.item_add()
        else:
            error(ERROR_UNKNOWN_SUBCOMMAND, token)

    # -------------------------------------------------------------
    # Database
    # -------------------------------------------------------------

    def database_commands(self, token: Token):
        """
        database_commands: CREATE [file_name] |
                           READ [file_name] |
                           WRITE |
                           EXPORT format file_name |
                           IMPORT format file_name |
                           DUMP
        :param token: next token
        """
        trace('database_command', token)

        # Check subcommand
        if token.tid not in LEX_DATABASE:
            error('invalid database action', token)
            return

        # Process actions
        if token.tid in [Tid.CREATE, Tid.READ]:

            # Get file name
            tok = self.get_token()
            if tok.tid == Tid.EOS:
                file_name = DEFAULT_DATABASE_NAME
                trace('no file name', file_name)
            elif tok.tid == Tid.FILE:
                file_name = tok.value
                trace('file name', file_name)
            else:
                error(ERROR_BAD_FILENAME, token)
                return

            # Run command
            if token.tid == Tid.READ:
                trace('read', file_name)
                print(self.cp.database_read(file_name))
            elif token.tid == Tid.CREATE:
                print(self.cp.database_create(file_name))
            else:
                error(ERROR_UNKNOWN_COMMAND, token)  # should never get here

        elif token.tid == Tid.WRITE:
            trace('write', token.value)
            print(self.cp.database_write())

        elif token.tid == Tid.EXPORT:
            tok = self.get_token()
            trace('export', tok)
            if tok.tid in [Tid.FMT_JSON, Tid.FMT_SQL]:
                output_format = FileFormat.FORMAT_JSON if tok.tid == Tid.FMT_JSON else FileFormat.FORMAT_SQL
                tok = self.get_token()
                trace('export', output_format, tok)
                if tok.tid == Tid.FILE:
                    print(self.cp.database_export(tok.value, output_format))
                else:
                    error(ERROR_BAD_FILENAME, tok)
            else:
                error(ERROR_BAD_FORMAT, tok)

        elif token.tid == Tid.DUMP:
            self.cp.database_dump()

        elif token.tid == Tid.REPORT:
            self.cp.database_report()

        else:
            error(ERROR_UNKNOWN_COMMAND, token)  # should never get here

    # -------------------------------------------------------------
    # Misc
    # -------------------------------------------------------------

    @staticmethod
    def misc_commands(token: Token):
        """
        misc_commands: TRACE |
        :param token: input token
        """
        trace('misc_command', token)
        if token.tid == Tid.TRACE:
            trace_toggle()
        else:
            error(ERROR_UNKNOWN_COMMAND, token)

    def quit(self, keyboard_interrupt: bool):
        """
        Terminate the parser
        :param keyboard_interrupt: program terminated by ctrl-c?
        """
        trace('quit')
        self.cp.quit_command(keyboard_interrupt)

    # -------------------------------------------------------------
    # General
    # -------------------------------------------------------------

    def action_command(self, cmd_token: Token):
        """
        action_command : DB subcommand |
                         ITEM subcommand |
                         FIELD subcommand |
                         TAG subcommand
        :param cmd_token: command token
        """
        trace('action_command', cmd_token)
        tok = self.get_token()
        if cmd_token.tid == Tid.DATABASE:
            self.database_commands(tok)
        elif cmd_token.tid == Tid.ITEM:
            self.item_command(tok)
        elif cmd_token.tid == Tid.FIELD:
            self.field_command(tok)
        elif cmd_token.tid == Tid.TAG:
            self.tag_command(tok)
        else:
            error(ERROR_UNKNOWN_COMMAND, 'here', cmd_token)  # should never get here

    def command(self):
        """
        A command can be either an action command, a program control command or empty.
        command : action_command |
                  misc_command |
                  empty
        """
        token = self.lexer.next_token()
        trace('command', token)
        if token.tid in LEX_ACTIONS:
            self.action_command(token)
        elif token.tid in LEX_MISC:
            self.misc_commands(token)
        elif token.tid == Tid.EOS:
            pass
        else:
            error(ERROR_UNKNOWN_COMMAND, token)

    def execute(self, command: str):
        """
        Parse and execute command
        :param command: command to parse/execute
        """
        self.cmd = command.strip()
        self.lexer.input(self.cmd)
        return self.command()


if __name__ == '__main__':
    pass
    # parser = Parser()
    # while True:
    #     try:
    #         input_command = input('db> ')
    #         input_command = input_command.strip()
    #         if len(input_command) > 0:
    #             if parser.execute(input_command):
    #                 # quit received
    #                 print('Exiting..')
    #                 break
    #     except (KeyboardInterrupt, EOFError):
    #         break
