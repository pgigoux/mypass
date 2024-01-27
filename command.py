from enum import Enum, auto
from os.path import exists
from typing import Callable
from db import Database, DEFAULT_DATABASE_NAME
from response import ResponseGenerator, Response
from sql import NAME_TAG_TABLE, NAME_FIELD_TABLE, NAME_ITEMS
from sql import MAP_TAG_ID, MAP_TAG_NAME, MAP_TAG_COUNT
from sql import MAP_FIELD_NAME, MAP_FIELD_COUNT
from sql import INDEX_ITEMS_NAME, INDEX_ITEMS_DATE, INDEX_ITEM_NOTE
from utils import get_password, get_timestamp, print_line, trace

NO_DATABASE = 'no database'

# Keys used to access the elements in the dictionary returned by item_print
KEY_ID = 'id'
KEY_NAME = 'name'
KEY_TIMESTAMP = 'timestamp'
KEY_NOTE = 'note'
KEY_TAGS = 'tags'
KEY_FIELDS = 'fields'


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
        self.resp = ResponseGenerator()
        self.confirm = confirm

    def db_loaded(self, overwrite=False) -> bool:
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

    def decrypt_value(self, value: str) -> str:
        return self.db.crypt_key.decrypt_str2str(value)

    # -----------------------------------------------------------------
    # Database commands
    # -----------------------------------------------------------------

    def database_create(self, file_name=DEFAULT_DATABASE_NAME) -> Response:
        """
        Create an empty database
        :param file_name: database file name
        """
        trace('database_create', file_name)
        if self.db_loaded(overwrite=True):
            return self.resp.warning('database not created')

        # Check whether the file exists already.
        # Create an empty database if that's not the case.
        if exists(file_name):
            return self.resp.error(f'database {file_name} already exists')
        else:
            self.file_name = file_name
            self.db = Database(file_name, get_password())
            return self.resp.ok(f'created database {file_name}')

    def database_read(self, file_name: str) -> Response:
        """
        Read database into memory
        :param file_name: database file name
        :return:
        """
        trace('database_read', file_name)
        if self.db_loaded(overwrite=True):
            return self.resp.warning(f'database {file_name} not read')

        trace(f'Reading from {file_name}')
        try:
            self.db = Database(file_name, get_password())
            self.db.read()
            self.file_name = file_name
            return self.resp.ok(f'read database {file_name}')
        except Exception as e:
            self.db = None
            self.file_name = DEFAULT_DATABASE_NAME
            return self.resp.exception(f'failed to read database {file_name}', e)

    def database_write(self) -> Response:
        trace('database_write')
        if self.db_loaded():
            assert isinstance(self.db, Database)
            trace(f'Writing to {self.file_name}')
            try:
                self.db.write()
                return self.resp.ok(f'database written to {self.file_name}')
            except Exception as e:
                return self.resp.exception(f'cannot write database to {self.file_name}', e)
        else:
            return self.resp.warning(NO_DATABASE)

    def database_export(self, file_name: str, output_format: FileFormat) -> Response:
        trace('database_export', file_name)
        if self.db_loaded():
            assert isinstance(self.db, Database)
            try:
                if output_format == FileFormat.FORMAT_JSON:
                    self.db.export_to_json(file_name)
                else:
                    self.db.sql.export_to_sql(file_name)
                return self.resp.ok(f'database exported to {file_name}')
            except Exception as e:
                return self.resp.exception(f'cannot export database', e)
        else:
            return self.resp.warning(NO_DATABASE)

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
        if self.db_loaded():
            assert isinstance(self.db, Database)
            print_line()
            self.db.dump()
            print_line()

    def database_report(self):
        """
        Print a database report to the terminal (debugging)
        """
        if self.db_loaded():
            assert isinstance(self.db, Database)
            self.db.database_report()

    # -----------------------------------------------------------------
    # Tag table commands
    # -----------------------------------------------------------------

    def tag_table_list(self) -> Response:
        """
        List all tags
        :return: response
        """
        if self.db_loaded():
            assert isinstance(self.db, Database)
            return self.resp.ok(self.db.sql.get_tag_table_list())
        else:
            return self.resp.warning(NO_DATABASE)

    def tag_table_count(self) -> Response:
        """
        Print tag count (or how many there are)
        :return: response
        """
        if self.db_loaded():
            assert isinstance(self.db, Database)
            return self.resp.ok(self.db.sql.get_table_count(NAME_TAG_TABLE))
        else:
            return self.resp.warning(NO_DATABASE)

    def tag_table_search(self, pattern: str) -> Response:
        """
        Search for tags matching a pattern
        :param pattern: regexp pattern
        :return: response
        """
        trace('tag_search', pattern)
        if self.db_loaded():
            assert isinstance(self.db, Database)
            return self.resp.ok(self.db.sql.search_tag_table(pattern))
        else:
            return self.resp.warning(NO_DATABASE)

    def tag_table_add(self, name: str) -> Response:
        """
        Add new tag
        :param name: tag name
        :return: response
        """
        if self.db_loaded():
            assert isinstance(self.db, Database)
            tag_mapping = self.db.sql.get_tag_table_name_mapping()
            if name in tag_mapping:
                return self.resp.error(f'tag {name} already exists')
            else:
                t_id = self.db.sql.insert_into_tag_table(None, name)
                return self.resp.ok(f'Added tag {name} with id {t_id}')
        else:
            return self.resp.warning(NO_DATABASE)

    def tag_table_rename(self, old_name: str, new_name: str) -> Response:
        """
        Rename existing tag
        :param old_name: old tag name
        :param new_name: new tag name
        :return: response
        """
        if self.db_loaded():
            assert isinstance(self.db, Database)
            if self.db.sql.rename_tag_table_entry(old_name, new_name) == 0:
                return self.resp.error(f'cannot rename tag {old_name}')
            else:
                return self.resp.ok(f'tag {old_name} -> {new_name}')
        else:
            return self.resp.warning(NO_DATABASE)

    def tag_table_delete(self, name: str) -> Response:
        """
        Delete tag
        :param name: tag name
        :return: response
        """
        if self.db_loaded():
            assert isinstance(self.db, Database)
            self.db.sql.update_tag_table_counters()
            tag_mapping = self.db.sql.get_tag_table_name_mapping()
            if name in tag_mapping:
                if tag_mapping[name][MAP_TAG_COUNT] == 0:
                    n = self.db.sql.delete_from_tag_table(name)
                    return self.resp.ok(f'removed {n} tags')
                else:
                    return self.resp.error(f'tag {name} is being used')
            else:
                return self.resp.error(f'tag {name} does not exist')
        else:
            return self.resp.warning(NO_DATABASE)

    # -----------------------------------------------------------------
    # Field table commands
    # -----------------------------------------------------------------

    def field_table_list(self) -> Response:
        """
        List all fields
        :return: response
        """
        trace('field_list')
        if self.db_loaded():
            assert isinstance(self.db, Database)
            return self.resp.ok(self.db.sql.get_field_table_list())
        else:
            return self.resp.warning(NO_DATABASE)

    def field_table_count(self) -> Response:
        """
        Print field count (or how many there are)
        :return: response
        """
        trace('field_count')
        if self.db_loaded():
            assert isinstance(self.db, Database)
            return self.resp.ok(self.db.sql.get_table_count(NAME_FIELD_TABLE))
        else:
            return self.resp.warning(NO_DATABASE)

    def field_table_search(self, pattern: str) -> Response:
        """
        Search for fields matching a pattern
        :param pattern: regexp pattern
        :return: response
        """
        trace('field_search', pattern)
        if self.db_loaded():
            assert isinstance(self.db, Database)
            return self.resp.ok(self.db.sql.search_field_table(pattern))
        else:
            return self.resp.warning(NO_DATABASE)

    def field_table_add(self, name: str, sensitive_flag: bool) -> Response:
        """
        Add new field
        :param name: field name
        :param sensitive_flag: sensitive?
        :return: response
        """
        trace('field_add', name, sensitive_flag)
        if self.db_loaded():
            assert isinstance(self.db, Database)
            field_mapping = self.db.sql.get_field_table_name_mapping()
            if name in field_mapping:
                return self.resp.error(f'field {name} already exists')
            else:
                f_id = self.db.sql.insert_into_field_table(None, name, sensitive_flag)
                return self.resp.ok(f'Added field {name} with id {f_id}')
        else:
            return self.resp.warning(NO_DATABASE)

    def field_table_rename(self, old_name: str, new_name: str) -> Response:
        """
        Rename existing tag
        :param old_name: old field name
        :param new_name: new field name
        :return: response
        """
        if self.db_loaded():
            assert isinstance(self.db, Database)
            if self.db.sql.rename_field_table_entry(old_name, new_name) == 0:
                return self.resp.error(f'cannot rename field {old_name}')
            else:
                return self.resp.ok(f'field {old_name} -> {new_name}')
        else:
            return self.resp.warning(NO_DATABASE)

    def field_table_delete(self, name: str) -> Response:
        """
        Delete field from field table
        :param name: field name
        :return: response
        """
        trace('field_delete', name)
        if self.db_loaded():
            assert isinstance(self.db, Database)
            self.db.sql.update_field_table_counters()
            field_mapping = self.db.sql.get_field_table_name_mapping()
            if name in field_mapping:
                if field_mapping[name][MAP_FIELD_COUNT] == 0:
                    n = self.db.sql.delete_from_field_table(name)
                    return self.resp.ok(f'removed {n} fields')
                else:
                    return self.resp.error(f'field {name} is being used')
            else:
                return self.resp.error(f'field {name} does not exist')
        else:
            return self.resp.warning(NO_DATABASE)

    # -----------------------------------------------------------------
    # Tags commands
    # -----------------------------------------------------------------

    # -----------------------------------------------------------------
    # Item commands
    # -----------------------------------------------------------------
 
    def item_list(self) -> Response:
        """
        List all items
        """
        trace('item_list')
        if self.db_loaded():
            assert isinstance(self.db, Database)
            return self.resp.ok(self.db.sql.get_item_list())
        else:
            return self.resp.warning(NO_DATABASE)

    def item_count(self) -> Response:
        """
        Print the number of items
        :return:
        """
        trace('item_count')
        if self.db_loaded():
            assert isinstance(self.db, Database)
            return self.resp.ok(self.db.sql.get_table_count(NAME_ITEMS))
        else:
            return self.resp.warning(NO_DATABASE)

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
        if self.db_loaded():
            assert isinstance(self.db, Database)
            item_list = self.db.search(pattern, item_name_flag=name_flag, tag_flag=tag_flag,
                                       field_name_flag=field_name_flag, field_value_flag=field_value_flag,
                                       note_flag=note_flag)
            return self.resp.ok(item_list)
        else:
            return self.resp.warning(NO_DATABASE)

    def item_get(self, item_id: int) -> Response:
        """
        Get item as a dictionary
        :param item_id: item id
        """
        trace('print_item', item_id)
        if self.db_loaded():
            print_line()
            assert isinstance(self.db, Database)

            # Get item and field information
            tag_mapping = self.db.sql.get_tag_table_id_mapping()
            field_mapping = self.db.sql.get_field_table_id_mapping()
            tag_list = self.db.sql.get_tag_list(item_id=item_id)
            field_list = self.db.sql.get_field_list(item_id=item_id)
            item_list = self.db.sql.get_item_list(item_id=item_id)
            if len(item_list) > 0:
                item = item_list[0]
                d = {KEY_ID: item_id,
                     KEY_NAME: item[INDEX_ITEMS_NAME],
                     KEY_TIMESTAMP: item[INDEX_ITEMS_DATE],
                     KEY_NOTE: item[INDEX_ITEM_NOTE],
                     KEY_TAGS: [tag_mapping[t_id][MAP_TAG_NAME] for _, t_id, _ in tag_list],
                     KEY_FIELDS: [(f_id, field_mapping[field_id][MAP_FIELD_NAME], f_value, f_encrypted)
                                  for f_id, field_id, _, f_value, f_encrypted in field_list],
                     }
                return self.resp.ok(d)
            else:
                return self.resp.error(f'item {item_id} does not exist')
        else:
            return self.resp.warning(NO_DATABASE)

    def item_add(self, item_name: str, tag_list: list, note: str) -> Response:
        """
        Add/create new item
        :param item_name: item name
        :param tag_list: tag name list
        :param note: note
        """
        trace('item_add', item_name, tag_list, note)
        if self.db_loaded():
            item_id = self.db.sql.insert_into_items(None, item_name, get_timestamp(), note)
            trace('item_id', item_id)
            if tag_list:
                tag_mapping = self.db.sql.get_tag_table_name_mapping()
                for tag in tag_list:
                    trace('adding tag', tag)
                    self.db.sql.insert_into_tags(None, tag_mapping[tag][MAP_TAG_ID], item_id)
            return self.resp.ok(f'added {item_id}')
        else:
            return self.resp.warning(NO_DATABASE)

    def item_delete(self, item_id: int) -> Response:
        """
        Delete item
        :param item_id: item id
        """
        trace(f'item_delete {item_id}')
        if self.db_loaded():
            assert isinstance(self.db, Database)
            n_tags = self.db.sql.delete_from_tags(item_id)
            n_fields = self.db.sql.delete_from_fields(item_id)
            if self.db.sql.delete_from_items(item_id) > 0:
                # self.db.sql.update_counters()
                return self.resp.ok(f'removed item {item_id}: {n_tags} tags and {n_fields} fields')
            else:
                return self.resp.error(f'Item {item_id} does not exist: {n_tags} tags, {n_fields} fields')
        else:
            return self.resp.warning(NO_DATABASE)

    def item_copy(self, item_id: int) -> Response:
        """
        Create a copy of an item with a different id
        The field collection is recreated and the timestamp updated.
        :param item_id: item id
        """
        trace('item_copy', item_id)
        if self.db_loaded():
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
                    return self.resp.ok(f'added item {new_item_id}, {len(tag_list)} tags, {len(field_list)} fields')
            else:
                return self.resp.error(f'item {item_id} does not exist')
        else:
            return self.resp.warning(NO_DATABASE)

    def item_update(self, item_id: int, item_name: str, note: str) -> Response:
        """
        Update item contents
        :param item_id: item id
        :param item_name: item name
        :param note: item note
        """
        if self.db_loaded():
            if item_name or note:
                n = self.db.sql.update_item(item_id, item_name, get_timestamp(), note)
                if n > 0:
                    return self.resp.ok(f'updated {n} items')
                else:
                    self.resp.warning('no items updated')
            else:
                self.resp.warning('nothing to update')
        else:
            return self.resp.warning(NO_DATABASE)

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
