from db import DEFAULT_DATABASE_NAME
from command import CommandProcessor, FileFormat
from command import KEY_DICT_ID, KEY_DICT_NAME, KEY_DICT_TIMESTAMP, KEY_DICT_NOTE, KEY_DICT_TAGS, KEY_DICT_FIELDS
from lexer import Lexer, Token, Tid
from lexer import LEX_ACTIONS, LEX_DATABASE, LEX_MISC, LEX_VALUE, LEX_STRING
from utils import error, trace, confirm, get_crypt_key, trace_toggle, sensitive_mark, timestamp_to_string

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
        self.cp = CommandProcessor(confirm_callback=confirm, crypt_callback=get_crypt_key)

    def get_token(self) -> Token:
        """
        Get next token from the lexer
        :return: token id and value
        """
        token = self.lexer.next_token()
        trace('parser, get_token', token)
        return token

    # -------------------------------------------------------------
    # Tag
    # -------------------------------------------------------------

    @staticmethod
    def _format_table_tag(tag_id: int, tag_name: str, tag_count: int) -> str:
        return f'{tag_id:2d} {tag_count:3d} {tag_name}'

    def tag_list(self):
        trace('parser, tag_list')
        r = self.cp.tag_table_list()
        if r.is_ok and r.is_list:
            for t_id, t_name, t_count in r.value:
                # print(f'{t_id:2d} {t_count:3d} {t_name}')
                print(self._format_table_tag(t_id, t_name, t_count))
        else:
            print(r)

    def tag_count(self):
        trace('parser, tag_count')
        r = self.cp.tag_table_count()
        if r.is_ok:
            print(r.value)
        else:
            print(r)

    def tag_search(self, tok: Token):
        trace('parser, tag_search', tok)
        r = self.cp.tag_table_search(tok.value)
        if r.is_ok and r.is_list:
            for t_id, t_name, t_count in r.value:
                print(self._format_table_tag(t_id, t_name, t_count))
        else:
            print(r)

    def tag_add(self, tok: Token):
        trace('parser, tag_add', tok)
        print(self.cp.tag_table_add(tok.value))

    def tag_rename(self, tok1: Token, tok2: Token):
        trace('parser, tag_rename', tok1, tok2)
        print(self.cp.tag_table_rename(tok1.value, tok2.value))

    def tag_delete(self, tok: Token):
        trace('parser, tag_delete', tok)
        print(self.cp.tag_table_delete(tok.value))

    def tag_command(self, token: Token):
        """
        tag_command : TAG subcommand
        :param token: subcommand token
        """
        trace('parser, tag_command', token)
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
                    trace('parser, tag search', tok)
                    self.tag_search(tok)
                else:
                    trace('parser, tag delete', tok)
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
        trace('parser, field_list')
        r = self.cp.field_table_list()
        if r.is_ok and r.is_list:
            for f_id, f_name, f_sensitive, f_count in r.value:
                print(self._format_table_field(f_id, f_name, f_sensitive, f_count))
        else:
            print(r)

    def field_count(self):
        trace('parser, field_count')
        r = self.cp.field_table_count()
        if r.is_ok:
            print(r.value)
        else:
            print(r)

    def field_search(self, tok: Token):
        trace('parser, field_search', tok)
        r = self.cp.field_table_search(tok.value)
        if r.is_ok and r.is_list:
            for f_id, f_name, f_sensitive, f_count in r.value:
                print(self._format_table_field(f_id, f_name, f_sensitive, f_count))
        else:
            print(r)

    def field_add(self, tok: Token, sensitive: bool):
        trace('parser, field_add', tok)
        print(self.cp.field_table_add(tok.value, sensitive))

    def field_rename(self, tok1: Token, tok2: Token):
        trace('parser, field_rename', tok1, tok2)
        print(self.cp.field_table_rename(tok1.value, tok2.value))

    def field_delete(self, tok: Token):
        trace('parser, field_delete', tok)
        print(self.cp.field_table_delete(tok.value))

    def field_command(self, token: Token):
        """
        field_command : FIELD subcommand
        :param token: subcommand token
        """
        trace('parser, field_command', token)
        if token.tid == Tid.LIST:
            self.field_list()
        elif token.tid == Tid.COUNT:
            self.field_count()
        elif token.tid in [Tid.SEARCH, Tid.DELETE]:
            tok = self.get_token()
            if tok.tid in LEX_STRING:
                if token.tid == Tid.SEARCH:
                    trace('parser, field search', tok)
                    self.field_search(tok)
                else:
                    trace('parser, field delete', tok)
                    self.field_delete(tok)
            else:
                error('bad/missing field name', tok)
        elif token.tid == Tid.ADD:
            tok = self.get_token()
            trace('parser, field add', tok)
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

    def item_options(self) -> dict | None:
        """
        Get item add/edit options
        :return: dictionary with options, or None if unknown option
        """
        d = {Tid.SW_SENSITIVE: False,
             Tid.SW_NAME: None,
             Tid.SW_NOTE: None,
             Tid.SW_MULTILINE_NOTE: False,
             Tid.SW_TAG: [],
             Tid.SW_FIELD_NAME: None,
             Tid.SW_FIELD_VALUE: None
             }
        while True:
            token = self.get_token()
            trace('parser, token', token)
            if token.tid == Tid.SW_NAME:
                t1 = self.get_token()
                trace('parser, found name', t1)
                if t1.tid in LEX_STRING:
                    d[Tid.SW_NAME] = t1.value
                else:
                    error(f'bad name option {t1}')
            elif token.tid == Tid.SW_TAG:
                t1 = self.get_token()
                trace('parser, found tag', t1, d)
                if t1.tid == Tid.NAME:
                    d[Tid.SW_TAG].append(t1.value)
                else:
                    error(f'bad tag {t1}')
            elif token.tid == Tid.SW_FIELD_NAME:
                t1 = self.get_token()
                trace('parser, found field name', t1)
                if t1.tid == Tid.NAME:
                    d[Tid.SW_FIELD_NAME] = t1.value
                else:
                    error(f'bad field name {t1}')
            elif token.tid == Tid.SW_FIELD_VALUE:
                t1 = self.get_token()
                trace('parser, found field value', t1)
                if t1.tid in LEX_VALUE:
                    d[Tid.SW_FIELD_VALUE] = t1.value
                else:
                    error(f'bad field value {t1}')
            elif token.tid == Tid.SW_NOTE:
                t1 = self.get_token()
                trace('parser, found note', t1)
                if t1.tid in LEX_VALUE:
                    d[Tid.SW_NOTE] = str(t1.value)
                else:
                    error(f'bad note {t1}')
            elif token.tid == Tid.SW_MULTILINE_NOTE:
                # TODO - decide how to handle this option
                d[Tid.SW_MULTILINE_NOTE] = True
            elif token.tid == Tid.EOS:
                trace('parser, eos')
                break
            else:
                error(f'unknown item option {token}')
                return None
        return d

    def item_list(self):
        trace('parser, item_list')
        r = self.cp.item_list()
        if r.is_ok and r.is_list:
            for i_id, i_name, i_timestamp, _ in r.value:
                print(self._format_item(i_id, i_name, i_timestamp))
        else:
            print(r)

    def item_count(self):
        trace('parser, item_count')
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
        trace('parser, item_search_command', token)
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
            elif tok.tid == Tid.SW_FIELD_NAME:
                field_name_flag = True
            elif tok.tid == Tid.SW_FIELD_VALUE:
                field_value_flag = True
            elif tok.tid == Tid.SW_NOTE:
                note_flag = True

        # Enable search by item name if no flags were specified
        if not any((name_flag, tag_flag, field_name_flag, field_value_flag, note_flag)):
            name_flag = True

        trace('parser, to search', tok.value, name_flag, tag_flag, field_name_flag, field_value_flag, note_flag)
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
        trace('parser, item_add')
        opt = self.item_options()
        if opt is not None:
            item_name = opt[Tid.SW_NAME]
            tag_list = opt[Tid.SW_TAG]
            note = opt[Tid.SW_NOTE] if opt[Tid.SW_NOTE] is not None else ''
            trace('parser, item_add', item_name, tag_list, note)
            if item_name is not None:
                print(self.cp.item_add(item_name, tag_list, note))
            else:
                error('no item name')

    def item_delete(self, token: Token):
        """
        Delete existing item
        :param token: item id token
        """
        trace('parser, item_delete', token)
        print(self.cp.item_delete(token.value))

    def item_copy(self, token: Token):
        """
        Duplicate item
        :param token: item id token
        """
        trace('parser, item_copy', token)
        print(self.cp.item_copy(token.value))

    def item_update(self, token: Token):
        """
        Edit existing item
        :param token: item id token
        """
        trace('parser, item_update', token)
        opt = self.item_options()
        if opt is not None:
            item_name = opt[Tid.SW_NAME]
            note = opt[Tid.SW_NOTE]
            trace('parser, item_update', item_name, note)
            if item_name is not None or note is not None:
                print(self.cp.item_update(token.value, item_name, note))
            else:
                error('missing item name or note')

    def item_tag_command(self, token: Token):
        """
        Add tag to item
        :param token: subcommand token
        """
        trace('parser, item_tag_command', token)
        if self.default_item_id is not None:
            tok = self.get_token()
            if tok.tid == Tid.NAME:
                if token.tid == Tid.ADD:
                    trace('parser, tag add', tok)
                    print(self.cp.tag_add(self.default_item_id, tok.value))
                elif token.tid == Tid.DELETE:
                    trace('parser, tag delete', tok)
                    print(self.cp.tag_delete(self.default_item_id, tok.value))
                else:
                    error('Invalid tag subcommand', token)
            else:
                error('tag name expected', tok)
        else:
            error('no item selected')

    def item_field_add_command(self):
        trace('parser, item_field_add_command')
        tok1 = self.get_token()
        tok2 = self.get_token()
        if tok1.tid == Tid.NAME and tok2.tid in LEX_VALUE:
            print(self.cp.field_add(self.default_item_id, tok1.value, tok2.value))
        else:
            error('missing or bad field name or value')

    def item_field_delete_command(self):
        trace('parser, item_field_delete_command')
        tok = self.get_token()
        if tok.tid == Tid.INT:
            print(self.cp.field_delete(self.default_item_id, tok.value))
        else:
            error('bad field id')

    def item_field_update_command(self):
        trace('parser, item_field_update_command')
        tok = self.get_token()
        if tok.tid == Tid.INT:
            opt = self.item_options()
            if opt is not None:
                field_name = opt[Tid.SW_FIELD_NAME]
                field_value = opt[Tid.SW_FIELD_VALUE]
                trace('parser, item_field_update', field_name, field_value)
                if field_name is not None or field_value is not None:
                    print(self.cp.field_update(self.default_item_id, tok.value, field_name, field_value))
                else:
                    error('must specify field name or value')
        else:
            error('bad or missing field id')

    def item_field_command(self, token: Token):
        """
        TODO
        :param token:
        :return:
        """
        trace('parser, item_field_command', token)
        if self.default_item_id is not None:
            if token.tid == Tid.ADD:
                self.item_field_add_command()
            elif token.tid == Tid.DELETE:
                self.item_field_delete_command()
            elif token.tid == Tid.UPDATE:
                self.item_field_update_command()
            else:
                error('unknown item subcommand', token)
        else:
            error('no item selected')

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
            print(f'id:    {d[KEY_DICT_ID]}')
            print(f'name:  {d[KEY_DICT_NAME]}')
            print(f'date:  {timestamp_to_string(d[KEY_DICT_TIMESTAMP])}')
            print(f'tags:  {d[KEY_DICT_TAGS]}')
            print('fields:')
            for f_id, f_name, f_value, f_encrypted in d[KEY_DICT_FIELDS]:
                f_value = self.cp.decrypt_value(f_value) if f_encrypted and show_encrypted else f_value
                print(f'  {f_id:4d} {sensitive_mark(f_encrypted)} {f_name} {f_value}')
                del f_value
            print('note:')
            if len(d[KEY_DICT_NOTE]) > 0:
                print(f'{d[KEY_DICT_NOTE]}')
        else:
            print(r)

    def item_command(self, token: Token):
        """
        item_command : ITEM subcommand
        :param token: subcommand token
        """
        trace('parser, item_command', token)
        if token.tid == Tid.LIST:
            self.item_list()
        elif token.tid == Tid.PRINT:
            tok = self.get_token()
            if tok.tid == Tid.EOS and self.default_item_id is not None:
                self.item_print(Token(Tid.INT, self.default_item_id))
            elif tok.tid == Tid.INT:
                self.item_print(tok)
            else:
                error('item id expected', tok)
        elif token.tid in [Tid.USE, Tid.DELETE, Tid.COPY, Tid.UPDATE]:
            tok = self.get_token()
            trace('parser, item print, dump, delete, copy, tag, field', tok)
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
            trace('parser, item tag', tok)
            if tok.tid in [Tid.ADD, Tid.DELETE, Tid.RENAME]:
                self.item_tag_command(tok)
            else:
                error('Invalid item tag subcommand', tok)
        elif token.tid == Tid.FIELD:
            tok = self.get_token()
            trace('parser, item field', tok)
            if tok.tid in [Tid.ADD, Tid.DELETE, Tid.RENAME, Tid.UPDATE]:
                self.item_field_command(tok)
            else:
                error('Invalid item tag subcommand', tok)
        elif token.tid == Tid.COUNT:
            trace('parser, item count', token)
            self.item_count()
        elif token.tid == Tid.SEARCH:
            tok = self.get_token()
            trace('parser, item search', tok)
            if tok.tid in LEX_STRING:
                self.item_search(tok)
            else:
                error('pattern expected')
        elif token.tid == Tid.ADD:
            trace('parser, item add', token)
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
        trace('parser, database_command', token)

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
                trace('parser, no file name', file_name)
            elif tok.tid == Tid.FILE:
                file_name = tok.value
                trace('parser, file name', file_name)
            else:
                error(ERROR_BAD_FILENAME, token)
                return

            # Run command
            if token.tid == Tid.READ:
                trace('parser, read', file_name)
                print(self.cp.database_read(file_name))
            elif token.tid == Tid.CREATE:
                print(self.cp.database_create(file_name))
            else:
                error(ERROR_UNKNOWN_COMMAND, token)  # should never get here

        elif token.tid == Tid.WRITE:
            trace('parser, write', token.value)
            print(self.cp.database_write())

        elif token.tid == Tid.EXPORT:
            tok = self.get_token()
            trace('parser, export', tok)
            if tok.tid in [Tid.FMT_JSON, Tid.FMT_SQL]:
                output_format = FileFormat.FORMAT_JSON if tok.tid == Tid.FMT_JSON else FileFormat.FORMAT_SQL
                tok = self.get_token()
                trace('parser, export', output_format, tok)
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
        trace('parser, misc_command', token)
        if token.tid == Tid.TRACE:
            trace_toggle()
        else:
            error(ERROR_UNKNOWN_COMMAND, token)

    def quit(self, keyboard_interrupt: bool):
        """
        Terminate the parser
        :param keyboard_interrupt: program terminated by ctrl-c?
        """
        trace('parser, quit')
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
        trace('parser, action_command', cmd_token)
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
        trace('parser, command', token)
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
