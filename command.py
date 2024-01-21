from enum import Enum, auto
from os.path import exists
from typing import Callable
from db import Database, DEFAULT_DATABASE_NAME
from error import ErrorHandler, Response
from sql import NAME_TAG_TABLE, NAME_FIELD_TABLE, NAME_TAGS, NAME_FIELDS, NAME_ITEMS
from sql import MAP_TAG_ID, MAP_TAG_NAME, MAP_TAG_COUNT
from sql import MAP_FIELD_ID, MAP_FIELD_NAME, MAP_FIELD_SENSITIVE, MAP_FIELD_COUNT
from utils import get_password, get_timestamp, timestamp_to_string, print_line, sensitive_mark, error, trace

NO_DATABASE = 'no database'


class FileFormat(Enum):
    FORMAT_JSON = auto()
    FORMAT_SQL = auto()


class CommandProcessor:

    def __init__(self, confirm: Callable):
        """
        The command processor handles the commands that interact with the database
        """
        self.file_name = ''  # database file name
        self.db = None  # database object
        self.err = ErrorHandler()
        self.confirm = confirm

    def _db_loaded(self, overwrite=False) -> bool:
        """
        Check whether there's a database in memory
        Prompt the user whether to overwrite the database if there is one in memory already
        :return: True if there's a database and the database can be overwritten, False otherwise
        """
        if self.db is None:
            return False
        elif overwrite:
            if self.confirm("There's a database already in memory"):
                return True
            else:
                return False
        else:
            return True

    # -----------------------------------------------------------------
    # Database commands
    # -----------------------------------------------------------------

    def database_create(self, file_name=DEFAULT_DATABASE_NAME) -> Response:
        """
        Create an empty database
        :param file_name: database file name
        """
        trace('database_create', file_name)
        if self._db_loaded(overwrite=True):
            return self.err.warning('database not created')

        # Check whether the file exists already.
        # Create an empty database if that's not the case.
        if exists(file_name):
            return self.err.error(f'database {file_name} already exists')
        else:
            self.file_name = file_name
            self.db = Database(file_name, get_password())
            return self.err.ok(f'created database {file_name}')

    def database_read(self, file_name: str) -> Response:
        """
        Read database into memory
        :param file_name: database file name
        :return:
        """
        trace('database_read', file_name)
        if self._db_loaded(overwrite=True):
            return self.err.warning(f'database {file_name} not read')

        trace(f'Reading from {file_name}')
        try:
            self.db = Database(file_name, get_password())
            self.db.read()
            self.file_name = file_name
            return self.err.ok(f'read database {file_name}')
        except Exception as e:
            self.db = None
            self.file_name = DEFAULT_DATABASE_NAME
            return self.err.exception(f'failed to read database {file_name}', e)

    def database_write(self) -> Response:
        trace('database_write')
        if self._db_loaded():
            assert isinstance(self.db, Database)
            trace(f'Writing to {self.file_name}')
            try:
                self.db.write()
                return self.err.ok(f'database written to {self.file_name}')
            except Exception as e:
                return self.err.exception(f'cannot write database to {self.file_name}', e)
        else:
            return self.err.warning(NO_DATABASE)

    def database_export(self, file_name: str, output_format: FileFormat) -> Response:
        trace('database_export', file_name)
        if self._db_loaded():
            assert isinstance(self.db, Database)
            try:
                if output_format == FileFormat.FORMAT_JSON:
                    self.db.export_to_json(file_name)
                else:
                    self.db.sql.export_to_sql(file_name)
                return self.err.ok(f'database exported to {file_name}')
            except Exception as e:
                return self.err.exception(f'cannot export database', e)
        else:
            return self.err.warning(NO_DATABASE)

    def database_import(self, file_name: str, input_format: FileFormat):
        """
        TODO - low priority
        :param file_name: input file name
        :param input_format: file format
        :return:
        """
        pass

    def database_dump(self):
        """
        Dump database contents to the terminal (debugging)
        :return:
        """
        trace('database_dump')
        if self._db_loaded():
            assert isinstance(self.db, Database)
            print_line()
            self.db.dump()
            print_line()

    def database_report(self):
        """
        Print a database report to the terminal (debugging)
        """
        if self._db_loaded():
            assert isinstance(self.db, Database)
            self.db.database_report()

    # -----------------------------------------------------------------
    # Tag commands
    # -----------------------------------------------------------------

    @staticmethod
    def _format_table_tag(tag_id: int, tag_name: str, tag_count: int) -> str:
        return f'{tag_id:2d} {tag_count:3d} {tag_name}'

    def tag_list(self):
        """
        List all tags
        """
        if self._db_loaded():
            assert isinstance(self.db, Database)
            return self.err.ok(self.db.sql.get_tag_table_list())
        else:
            return self.err.warning(NO_DATABASE)

    def tag_count(self) -> Response:
        """
        Print tag count (or how many there are)
        """
        if self._db_loaded():
            assert isinstance(self.db, Database)
            return self.err.ok(self.db.sql.get_table_count(NAME_TAG_TABLE))
        else:
            return self.err.warning(NO_DATABASE)

    def tag_search(self, pattern: str) -> Response:
        """
        Search for tags matching a pattern
        :param pattern: regexp pattern
        """
        trace('tag_search', pattern)
        if self._db_loaded():
            assert isinstance(self.db, Database)
            return self.err.ok(self.db.sql.search_tag_table(pattern))
        else:
            return self.err.warning(NO_DATABASE)

    def tag_add(self, name: str) -> Response:
        """
        Add new tag
        :param name: tag name
        :return:
        """
        if self._db_loaded():
            assert isinstance(self.db, Database)
            tag_mapping = self.db.sql.get_tag_table_name_mapping()
            if name in tag_mapping:
                return self.err.error(f'tag {name} already exists')
            else:
                t_id = self.db.sql.insert_into_tag_table(None, name)
                return self.err.ok(f'Added tag {name} with id {t_id}')
        else:
            return self.err.warning(NO_DATABASE)

    def tag_rename(self, old_name: str, new_name: str) -> Response:
        """
        Rename existing tag
        :param old_name: old tag name
        :param new_name: new tag name
        :return:
        """
        if self._db_loaded():
            assert isinstance(self.db, Database)
            if self.db.sql.rename_tag_table_entry(old_name, new_name) == 0:
                return self.err.error(f'cannot rename tag {old_name}')
            else:
                return self.err.ok(f'tag {old_name} -> {new_name}')
        else:
            return self.err.warning(NO_DATABASE)

    def tag_delete(self, name: str) -> Response:
        """
        Delete tag
        :param name: tag name
        :return:
        """
        if self._db_loaded():
            assert isinstance(self.db, Database)
            self.db.sql.update_tag_table_counters()
            tag_mapping = self.db.sql.get_tag_table_name_mapping()
            if name in tag_mapping:
                if tag_mapping[name][MAP_TAG_COUNT] == 0:
                    n = self.db.sql.delete_from_tag_table(name)
                    return self.err.ok(f'removed {n} tags')
                else:
                    return self.err.error(f'tag {name} is being used')
            else:
                return self.err.error(f'tag {name} does not exist')
        else:
            return self.err.warning(NO_DATABASE)

    # -----------------------------------------------------------------
    # Field commands
    # -----------------------------------------------------------------

    @staticmethod
    def _format_table_field(field_id: int, field_name: str, field_sensitive: bool, field_count: int) -> str:
        return f'{field_id:3d} {field_count:4d} {sensitive_mark(field_sensitive)} {field_name}'

    def field_list(self):
        """
        List all fields
        """
        trace('field_list')
        if self._db_loaded():
            assert isinstance(self.db, Database)
            for f_id, f_name, f_sensitive, f_count in self.db.sql.get_field_table_list():
                print(self._format_table_field(f_id, f_name, f_sensitive, f_count))

    def field_count(self):
        """
        Print field count (or how many there are)
        """
        trace('field_count')
        if self._db_loaded():
            assert isinstance(self.db, Database)
            print(self.db.sql.get_table_count(NAME_FIELD_TABLE))

    def field_search(self, pattern: str):
        """
        Search for fields matching a pattern
        :param pattern: regexp pattern
        """
        trace('field_search', pattern)
        if self._db_loaded():
            assert isinstance(self.db, Database)
            trace('field_search', pattern)
            if self._db_loaded():
                assert isinstance(self.db, Database)
                for f_id, f_name, f_sensitive, f_count in self.db.sql.search_field_table(pattern):
                    print(self._format_table_field(f_id, f_name, f_sensitive, f_count))

    def field_add(self, name: str, sensitive_flag: bool):
        """
        Add new field
        :param name: field name
        :param sensitive_flag: sensitive?
        :return:
        """
        trace('field_add', name, sensitive_flag)
        if self._db_loaded():
            assert isinstance(self.db, Database)
            field_mapping = self.db.sql.get_field_table_name_mapping()
            if name in field_mapping:
                error(f'field {name} already exists')
            else:
                f_id = self.db.sql.insert_into_field_table(None, name, sensitive_flag)
                print(f'Added field {name} with id {f_id}')

    def field_rename(self, old_name: str, new_name: str):
        """
        Rename existing tag
        :param old_name: old field name
        :param new_name: new field name
        :return:
        """
        if self._db_loaded():
            assert isinstance(self.db, Database)
            try:
                self.db.sql.rename_field_table_entry(old_name, new_name)
            except Exception as e:
                error(f'cannot rename tag {old_name} to {new_name}', e)

    def field_delete(self, name: str):
        """
        Delete field from field table
        :param name: field name
        """
        trace('field_delete', name)
        if self._db_loaded():
            assert isinstance(self.db, Database)
            field_mapping = self.db.sql.get_field_table_name_mapping()
            if name in field_mapping:
                if field_mapping[name][MAP_TAG_COUNT] == 0:
                    n = self.db.sql.delete_from_field_table(name)
                    print(f'removed {n} fields')
                else:
                    error(f'field {name} is being used')
            else:
                error(f'field {name} does not exist')

    # -----------------------------------------------------------------
    # Item commands
    # -----------------------------------------------------------------
    @staticmethod
    def _format_item(item_id: int, item_name: str, item_timestamp: int) -> str:
        return f'{item_id:5d}  {timestamp_to_string(item_timestamp, date_only=True)}  {item_name}'

    def item_list(self):
        """
        List all items
        """
        trace('item_list')
        if self._db_loaded():
            assert isinstance(self.db, Database)
            for item_id, item_name, item_timestamp, _ in self.db.sql.get_item_list():
                print(self._format_item(item_id, item_name, item_timestamp))

    def item_print(self, item_id: int, show_encrypted: bool):
        """
        Print item
        :param item_id: item id
        :param show_encrypted: print sensitive fields unencrypted
        """
        trace('print_item', item_id)
        if self._db_loaded():
            print_line()
            assert isinstance(self.db, Database)

            # Get item and field information
            tag_mapping = self.db.sql.get_tag_table_id_mapping()
            field_mapping = self.db.sql.get_field_table_id_mapping()
            tag_list = self.db.sql.get_tag_list(item_id=item_id)
            field_list = self.db.sql.get_field_list(item_id=item_id)
            item_list = self.db.sql.get_item_list(item_id=item_id)

            # Iterate over the list of items (it should be just one)
            if len(item_list) > 0:
                for i_id, i_name, i_timestamp, i_note in item_list:
                    print(f'id:    {i_id}')
                    print(f'name:  {i_name}')
                    print(f'date:  {timestamp_to_string(i_timestamp)}')
                    print(f'tags:  {[tag_mapping[t_id][MAP_TAG_NAME] for _, t_id, _ in tag_list]}')
                    print('fields:')
                    for f_id, field_id, _, f_value, f_encrypted in field_list:
                        f_name = field_mapping[field_id][MAP_FIELD_NAME]
                        f_value = self.db.crypt_key.decrypt_str2str(
                            f_value) if f_encrypted and show_encrypted else f_value
                        print(f'  {f_id:4d} {sensitive_mark(f_encrypted)} {f_name} {f_value}')
                        del f_value
                    print('note:')
                    if len(i_note) > 0:
                        print(f'{i_note}')
            else:
                error(f'item {item_id} does not exist')

    def item_count(self):
        """
        Print the number of items
        :return:
        """
        trace('item_count')
        if self._db_loaded():
            assert isinstance(self.db, Database)
            print(self.db.sql.get_table_count(NAME_ITEMS))

    def item_search(self, pattern: str, name_flag: bool, tag_flag: bool,
                    field_name_flag: bool, field_value_flag: bool, note_flag: bool):
        """
        Search for a string pattern in all items.
        :param pattern: pattern to search for
        :param name_flag: search in name?
        :param tag_flag: search in tags?
        :param field_name_flag: search in field names?
        :param field_value_flag: search in field values?
        :param note_flag: search in note?
        """
        trace('item_search', pattern, name_flag, tag_flag, field_name_flag, field_value_flag, note_flag)
        if self._db_loaded():
            assert isinstance(self.db, Database)
            item_list = self.db.search(pattern, item_name_flag=name_flag, tag_flag=tag_flag,
                                       field_name_flag=field_name_flag, field_value_flag=field_value_flag,
                                       note_flag=note_flag)
            for item_id, item_name, item_timestamp in item_list:
                print(self._format_item(item_id, item_name, item_timestamp))

    def item_delete(self, item_id: int):
        """
        Delete item
        :param item_id: item id
        """
        trace(f'item_delete {item_id}')
        if self._db_loaded():
            assert isinstance(self.db, Database)
            n_tags = self.db.sql.delete_from_tags(item_id)
            n_fields = self.db.sql.delete_from_fields(item_id)
            if self.db.sql.delete_from_items(item_id) > 0:
                print(f'removed item {item_id}: {n_tags} tags and {n_fields} fields')
            else:
                error(f'Item {item_id} does not exist: tags={n_tags}, fields={n_fields}')

    def item_copy(self, item_id: int):
        """
        Create a copy of an item with a different id
        The field collection is recreated and the timestamp updated.
        :param item_id: item id
        """
        trace('item_copy', item_id)
        if self._db_loaded():
            assert isinstance(self.db, Database)
            item_list = self.db.sql.get_item_list(item_id=item_id)
            tag_list = self.db.sql.get_tag_list(item_id=item_id)
            field_list = self.db.sql.get_field_list(item_id=item_id)
            if len(item_list) > 0:
                for i_id, i_name, i_timestamp, i_note in item_list:
                    new_item_id = self.db.sql.insert_into_items(None, 'Copy of ' + i_name, get_timestamp(), i_note)
                    for _, t_id, _ in tag_list:
                        self.db.sql.insert_into_tags(None, t_id, new_item_id)
                    for _, f_id, _, f_value, f_encrypted in field_list:
                        self.db.sql.insert_into_fields(None, f_id, new_item_id, f_value, f_encrypted)
                    print(f'added item {new_item_id}')
            else:
                print(f'item {item_id} does not exist')

    def item_add(self, item_name: str, tag_list: list, note: str):
        """
        Add/create new item
        :param item_name: item name
        :param tag_list: tag name list
        :param note: note
        """
        trace('item_add', item_name, tag_list, note)
        if self._db_loaded():
            item_id = self.db.sql.insert_into_items(None, item_name, get_timestamp(), note)
            trace('item_id', item_id)
            if tag_list:
                tag_mapping = self.db.sql.get_tag_table_name_mapping()
                for tag in tag_list:
                    trace('adding tag', tag)
                    self.db.sql.insert_into_tags(None, tag_mapping[tag][MAP_TAG_ID], item_id)
            print(f'added {item_id}')

    def item_update(self, item_id: int, item_name: str, note: str):
        """
        Update item contents
        :param item_id: item id
        :param item_name: item name
        :param note: item note
        """
        if self._db_loaded():
            if item_name or note:
                n = self.db.sql.update_item(item_id, item_name, get_timestamp(), note)
                print(f'updated {n} items')
            else:
                print('nothing to update')

    # -----------------------------------------------------------------
    # Misc commands
    # -----------------------------------------------------------------

    def quit_command(self, keyboard_interrupt: bool):
        """
        Command that will be called when the program exits
        """
        trace(f'quit_command {self.file_name}', keyboard_interrupt)


if __name__ == '__main__':
    pass
