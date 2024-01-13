from db import DEFAULT_DATABASE_NAME
from command import CommandProcessor, ExportFormat
from lexer import Lexer, Token, Tid
from lexer import LEX_ACTIONS, LEX_DATABASE, LEX_ITEM, LEX_TAG, LEX_FIELD, LEX_MISC, LEX_VALUES, LEX_STRINGS
from utils import error, trace, trace_toggle

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
        self.cp = CommandProcessor()

    def get_token(self) -> Token:
        """
        Get next token from the lexer
        :return: token id and value
        """
        token = self.lexer.next_token()
        trace('get_token', token)
        return token

    # -------------------------------------------------------------
    # Fields
    # -------------------------------------------------------------

    def field_command(self, token: Token):
        """
        field_command : FIELD subcommand
        :param token: subcommand token
        """
        trace('field_command', token)
        if token.tid == Tid.LIST:
            self.cp.field_list()
        elif token.tid == Tid.COUNT:
            self.cp.field_count()
        elif token.tid in [Tid.SEARCH, Tid.DELETE]:
            tok = self.get_token()
            if tok.tid in LEX_STRINGS:
                if token.tid == Tid.SEARCH:
                    trace('field search', tok)
                    self.cp.field_search(tok.value)
                else:
                    trace('field delete', tok)
                    self.cp.field_delete(tok.value)
            else:
                error('bad/missing field name', tok)
        elif token.tid == Tid.ADD:
            tok = self.get_token()
            trace('field add', tok)
            if tok.tid in LEX_STRINGS:
                s_tok = self.get_token()
                sensitive = True if s_tok.tid == Tid.SW_SENSITIVE else False
                self.cp.field_add(tok.value, sensitive)
        elif token.tid == Tid.RENAME:
            tok1 = self.get_token()
            tok2 = self.get_token()
            if tok1.tid in LEX_STRINGS and tok2.tid in LEX_STRINGS:
                self.cp.field_rename(tok1.value, tok2.value)
            else:
                error('bad tag name', tok1, tok2)
        else:
            error(ERROR_UNKNOWN_SUBCOMMAND, token)

    # -------------------------------------------------------------
    # Tag
    # -------------------------------------------------------------

    def tag_command(self, token: Token):
        """
        tag_command : TAG subcommand
        :param token: subcommand token
        """
        trace('tag_command', token)
        if token.tid == Tid.LIST:
            self.cp.tag_list()
        elif token.tid == Tid.COUNT:
            self.cp.tag_count()
        elif token.tid in [Tid.SEARCH, Tid.DELETE]:
            tok = self.get_token()
            if tok.tid in LEX_STRINGS:
                if token.tid == Tid.SEARCH:
                    trace('tag search', tok)
                    self.cp.tag_search(tok.value)
                else:
                    trace('tag delete', tok)
                    self.cp.tag_delete(tok.value)
            else:
                error('bad/missing tag name', tok)
        elif token.tid == Tid.ADD:
            tok = self.get_token()
            if tok.tid in LEX_STRINGS:
                self.cp.tag_add(tok.value)
        elif token.tid == Tid.RENAME:
            tok1 = self.get_token()
            tok2 = self.get_token()
            if tok1.tid in LEX_STRINGS and tok2.tid in LEX_STRINGS:
                self.cp.tag_rename(tok1.value, tok2.value)
            else:
                error('bad tag name', tok1, tok2)
        else:
            error(ERROR_UNKNOWN_SUBCOMMAND, token)

    # -------------------------------------------------------------
    # Item
    # -------------------------------------------------------------

    def item_search_command(self):
        """
        item_search_command: ITEM SEARCH NAME search_option_list
        :return:
        """
        tok = self.get_token()
        trace('item_search_command', tok)
        if tok.tid in LEX_STRINGS:
            pattern = tok.value
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
            self.cp.item_search(pattern, name_flag, tag_flag, field_name_flag, field_value_flag, note_flag)
        else:
            error('name expected')

    def item_print(self, token: Token):
        """
        item_print_command: PRINT [SW_SENSITIVE]
        :param token: item token
        """
        tok = self.get_token()
        if tok.tid == Tid.SW_SENSITIVE:
            self.cp.item_print(token.value, True)
        else:
            self.cp.item_print(token.value, False)

    def item_options(self, delete_flag=False) -> tuple[str, list, list, list, str, bool]:
        """
        Get item create/add/edit options
        :param delete_flag: accept SW_FIELD_DELETE?
        :return: tuple
        """
        item_name = ''
        tag_list = []
        field_list = []
        field_delete_list = []
        note = ""
        multiline_note = False
        while True:
            token = self.get_token()
            trace('-- token', token)
            if token.tid == Tid.SW_NAME:
                t1 = self.get_token()
                trace('found name', t1)
                if t1.tid in LEX_STRINGS:
                    item_name = t1.value
                else:
                    raise ValueError(f'bad item name {t1}')

            elif token.tid == Tid.SW_TAG:
                t1 = self.get_token()
                trace('found tag', t1)
                if t1.tid == Tid.NAME:
                    tag_list.append(t1.value)
                else:
                    raise ValueError(f'bad tag {t1}')

            elif token.tid == Tid.SW_FIELD:
                t1, t2 = self.get_token(), self.get_token()
                trace('found field', t1, t2)
                if t1.tid == Tid.NAME and t2.tid in LEX_VALUES:
                    field_list.append((t1.value, t2.value))
                else:
                    raise ValueError(f'bad field name/value {t1}')

            elif token.tid == Tid.SW_FIELD_DELETE:
                t1 = self.get_token()
                if delete_flag:
                    trace('found field delete', t1)
                    if t1.tid == Tid.NAME:
                        field_delete_list.append(t1.value)
                    else:
                        raise ValueError(f'bad field name {t1}')
                else:
                    raise ValueError(f'field delete not allowed {t1}')

            elif token.tid == Tid.SW_NOTE:
                t1 = self.get_token()
                trace('found note', t1)
                if t1.tid in LEX_STRINGS:
                    note = t1.value
                elif t1.tid == Tid.VALUE:
                    note = str(t1.value)
                else:
                    raise ValueError(f'bad note {t1}')

            elif token.tid == Tid.SW_MULTILINE_NOTE:
                trace('found note text')
                multiline_note = True

            elif token.tid == Tid.EOS:
                trace('eos')
                break

            else:
                raise ValueError(f'unknown item option {token}')

        # print(f'name="{item_name}", tags={tag_list}, fields={field_list}, field_delete={field_delete_list}'
        #       f' note="{note}", multi={multiline_note}')multiline_note

        return item_name, tag_list, field_list, field_delete_list, note, multiline_note

    def item_create(self):
        """
        item_create_command: ITEM CREATE [options]
        """
        # trace('item_create', )
        try:
            item_name, tag_list, field_list, _, note, multiline_flag = self.item_options()
            trace('item_create', item_name, tag_list, field_list, note, multiline_flag)
        except Exception as e:
            print(f'--- e=[{e}')
            error(str(e))
            return
        self.cp.item_create(item_name, tag_list, field_list, note, multiline_flag)

    def item_add(self, token: Token):
        """
        :param token: item id token
        """
        trace('item_add', token)
        try:
            item_name, tag_list, field_list, _, note, multiline_note = self.item_options()
            trace('item_add', item_name, tag_list, field_list, note, multiline_note)
            self.cp.item_add(token.value, item_name, tag_list, field_list, note, multiline_note)
        except Exception as e:
            error(str(e))

    def item_edit(self, token: Token):
        """
        :param token: item id token
        :return:
        """
        trace('item_edit', token)
        try:
            item_name, tag_list, field_list, field_delete_list, note, multiline_note = \
                self.item_options(delete_flag=True)
            trace('item_edit', item_name, tag_list, field_list, field_delete_list, note, multiline_note)
            self.cp.item_edit(token.value, item_name, tag_list, field_list, field_delete_list, note, multiline_note)
        except Exception as e:
            error(str(e))

    def item_command(self, token: Token):
        """
        item_command : ITEM subcommand
        :param token: subcommand token
        """
        trace('item_command', token)
        if token.tid == Tid.LIST:
            self.cp.item_list()
        elif token.tid in [Tid.PRINT, Tid.DUMP, Tid.DELETE, Tid.COPY]:
            tok = self.get_token()
            trace('print, dump, delete, copy', tok)
            if tok.tid == Tid.VALUE:
                if token.tid == Tid.PRINT:
                    self.item_print(tok)
                elif token.tid == Tid.DELETE:
                    self.cp.item_delete(tok.value)
                elif token.tid == Tid.COPY:
                    self.cp.item_copy(tok.value)
                else:
                    error('Unknown item subcommand', tok)
            else:
                error('item id expected')
        elif token.tid == Tid.COUNT:
            self.cp.item_count()
        elif token.tid == Tid.SEARCH:
            self.item_search_command()
        elif token.tid == Tid.CREATE:
            self.item_create()
        elif token.tid in [Tid.EDIT, Tid.ADD]:
            tok = self.get_token()
            trace('edit, add', tok)
            if tok.tid == Tid.VALUE:
                if token.tid == Tid.EDIT:
                    self.item_edit(tok)
                else:
                    self.item_add(tok)
            else:
                error('item id expected')
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
                self.cp.database_read(file_name)
            elif token.tid == Tid.CREATE:
                self.cp.database_create(file_name)
            else:
                error(ERROR_UNKNOWN_COMMAND, token)  # should never get here

        elif token.tid == Tid.WRITE:
            trace('write', token.value)
            self.cp.database_write()

        elif token.tid == Tid.EXPORT:
            tok = self.get_token()
            trace('export', tok)
            if tok.tid in [Tid.FMT_JSON, Tid.FMT_SQL]:
                output_format = ExportFormat.FORMAT_JSON if tok.tid == Tid.FMT_JSON else ExportFormat.FORMAT_SQL
                tok = self.get_token()
                trace('export', output_format, tok)
                if tok.tid == Tid.FILE:
                    self.cp.database_export(tok.value, output_format)
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
