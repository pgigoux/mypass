from enum import Enum, auto
from os.path import exists
from typing import Callable
from db import Database, DEFAULT_DATABASE_NAME
from response import ResponseGenerator, Response
from sql import NAME_TAG_TABLE, NAME_FIELD_TABLE, NAME_ITEMS
from sql import MAP_TAG_ID, MAP_TAG_NAME, MAP_TAG_COUNT
from sql import MAP_FIELD_ID, MAP_FIELD_NAME, MAP_FIELD_SENSITIVE, MAP_FIELD_COUNT
from sql import INDEX_ID, INDEX_ITEMS_NAME, INDEX_ITEMS_DATE, INDEX_ITEMS_NOTE
from sql import INDEX_FIELDS_FIELD_ID, INDEX_FIELDS_VALUE, INDEX_FIELDS_ENCRYPTED
from utils import get_timestamp, print_line, trace

NO_DATABASE = 'no database'

# Keys used to access the elements in the dictionary returned by item_print
KEY_DICT_ID = 'id'
KEY_DICT_NAME = 'name'
KEY_DICT_TIMESTAMP = 'timestamp'
KEY_DICT_NOTE = 'note'
KEY_DICT_TAGS = 'tags'
KEY_DICT_FIELDS = 'fields'


class FileFormat(Enum):
    """
    Export formats
    """
    FORMAT_JSON = auto()
    FORMAT_SQL = auto()


class CommandProcessor:
    """
    Class that's in charge of executing commands that interact with the database
    """

    def __init__(self, confirm_callback: Callable, crypt_callback: Callable):
        """
        The command processor handles the commands that interact with the database.
        Two callbacks are used, so it's up to the caller to decide how to prompt
        the user for action confirmations and the database encryption key.
        :param confirm_callback: function called to confirm action (True/False)
        :param crypt_callback: function to get the encryption key
        """
        self.file_name = ''  # database file name
        self.db = None  # database object
        self.resp = ResponseGenerator()
        self.confirm = confirm_callback
        self.crypt = crypt_callback

    # -----------------------------------------------------------------
    # Auxiliary functions
    # -----------------------------------------------------------------

    def get_database_name(self) -> str:
        """
        Return the database file name
        :return: database file name
        """
        return self.file_name

    def db_loaded(self, overwrite=False) -> bool:
        """
        Check whether there's a database in memory
        Prompt the user whether to overwrite the database if there is one in memory already
        :param: overwrite database if there's one in memory already?
        :return: True if there's a database and the database cannot be overwritten, False otherwise
        """
        if self.db is None:
            return False
        if overwrite:
            return not self.confirm("There's a database already in memory")
        else:
            return True

    def encrypt_value(self, value: str) -> str:
        """
        Auxiliary function used to encrypt a string value
        :param value: the value to encrypt
        :return:
        """
        return self.db.crypt_key.encrypt_str2str(value) if self.db.crypt_key is not None else value

    def decrypt_value(self, value: str) -> str:
        """
        Auxiliary routine used to decrypt a string value
        :param value:
        :return: encrypted value
        """
        return self.db.crypt_key.decrypt_str2str(value) if self.db.crypt_key is not None else value

    # -----------------------------------------------------------------
    # Database commands
    # -----------------------------------------------------------------

    def database_create(self, file_name=DEFAULT_DATABASE_NAME) -> Response:
        """
        Create an empty database
        :param file_name: new database file name
        :return: response
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
            self.db = Database(file_name, self.crypt())
            return self.resp.ok(f'created database {file_name}')

    def database_read(self, file_name: str) -> Response:
        """
        Read database into memory
        :param file_name: database file name
        :return: response
        """
        trace('database_read', file_name)
        if self.db_loaded(overwrite=True):
            return self.resp.warning(f'database {file_name} not read')

        trace(f'Reading from {file_name}')
        try:
            self.db = Database(file_name, self.crypt())
            self.db.read()
            self.file_name = file_name
            return self.resp.ok(f'read database {file_name}')
        except Exception as e:
            self.db = None
            self.file_name = DEFAULT_DATABASE_NAME
            return self.resp.exception(f'failed to read database {file_name}', e)

    def database_write(self) -> Response:
        """
        Write database to disk
        :return: response
        """
        trace('database_write')
        if self.db_loaded():
            trace(f'Writing to {self.file_name}')
            try:
                assert isinstance(self.db, Database)
                self.db.write()
                return self.resp.ok(f'database written to {self.file_name}')
            except Exception as e:
                return self.resp.exception(f'cannot write database to {self.file_name}', e)
        else:
            return self.resp.warning(NO_DATABASE)

    def database_export(self, file_name: str, output_format: FileFormat) -> Response:
        trace('database_export', file_name)
        if self.db_loaded():
            try:
                assert isinstance(self.db, Database)
                if output_format == FileFormat.FORMAT_JSON:
                    self.db.export_to_json(file_name)
                else:
                    self.db.sql.export_to_sql(file_name)
                return self.resp.ok(f'database exported to {file_name}')
            except Exception as e:
                return self.resp.exception('cannot export database', e)
        else:
            return self.resp.warning(NO_DATABASE)

    def database_import(self, file_name: str, input_format: FileFormat) -> Response:
        """
        TODO - low priority
        :param file_name: input file name
        :param input_format: file format
        :return:
        """
        trace('database_import', file_name, input_format)
        return self.resp.warning('not yet implemented')

    def database_dump(self):
        """
        Dump database contents to the terminal (debugging)
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
        trace('database_report')
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
        trace('tag_table_list')
        if self.db_loaded():
            try:
                assert isinstance(self.db, Database)
                return self.resp.ok(self.db.sql.get_tag_table_list())
            except Exception as e:
                return self.resp.exception('cannot list tag table', e)
        else:
            return self.resp.warning(NO_DATABASE)

    def tag_table_count(self) -> Response:
        """
        Print tag count (or how many there are)
        :return: response
        """
        trace('tag_table_count')
        if self.db_loaded():
            try:
                assert isinstance(self.db, Database)
                return self.resp.ok(self.db.sql.get_table_count(NAME_TAG_TABLE))
            except Exception as e:
                return self.resp.exception('cannot return tag table count', e)
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
            try:
                assert isinstance(self.db, Database)
                return self.resp.ok(self.db.sql.search_tag_table(pattern))
            except Exception as e:
                return self.resp.exception('cannot search tag table', e)
        else:
            return self.resp.warning(NO_DATABASE)

    def tag_table_add(self, name: str) -> Response:
        """
        Add new tag
        :param name: tag name
        :return: response
        """
        trace('tag_table_add', name)
        if self.db_loaded():
            try:
                assert isinstance(self.db, Database)
                tag_mapping = self.db.sql.get_tag_table_name_mapping()
                if name in tag_mapping:
                    return self.resp.error(f'tag {name} already exists')
                else:
                    t_id = self.db.sql.insert_into_tag_table(None, name)
                    return self.resp.ok(f'Added tag {name} with id {t_id}')
            except Exception as e:
                return self.resp.exception('cannot add tag to table', e)
        else:
            return self.resp.warning(NO_DATABASE)

    def tag_table_rename(self, old_name: str, new_name: str) -> Response:
        """
        Rename existing tag
        :param old_name: old tag name
        :param new_name: new tag name
        :return: response
        """
        trace('tag_table_rename', old_name, new_name)
        if self.db_loaded():
            try:
                assert isinstance(self.db, Database)
                if self.db.sql.rename_tag_table_entry(old_name, new_name) == 0:
                    return self.resp.error(f'cannot rename tag {old_name}')
                else:
                    return self.resp.ok(f'tag {old_name} -> {new_name}')
            except Exception as e:
                return self.resp.exception('cannot rename tag in table', e)
        else:
            return self.resp.warning(NO_DATABASE)

    def tag_table_delete(self, name: str) -> Response:
        """
        Delete tag
        :param name: tag name
        :return: response
        """
        trace('tag_table_delete', name)
        if self.db_loaded():
            try:
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
            except Exception as e:
                return self.resp.exception('cannot delete tag from table', e)
        else:
            return self.resp.warning(NO_DATABASE)

    def tag_table_import(self, file_name: str):
        """
        Import tags from a csv file
        :param file_name: input file name
        :return: response
        """
        trace('tag_table_import', file_name)
        if self.db_loaded():
            try:
                assert isinstance(self.db, Database)
                if self.db.sql.get_table_count(NAME_TAG_TABLE) == 0:
                    try:
                        self.db.tag_table_import(file_name)
                        return self.resp.ok(f'imported {self.db.sql.get_table_count(NAME_TAG_TABLE)} tags')
                    except Exception as e:
                        return self.resp.exception('cannot import tags', e)
                else:
                    return self.resp.error('database already has tags defined')
            except Exception as e:
                return self.resp.exception('cannot import tag table', e)
        else:
            return self.resp.warning(NO_DATABASE)

    def tag_table_export(self, file_name: str):
        """
        Export the tag table in csv format
        :param file_name: output file name
        :return: response
        """
        trace('tag_table_import', file_name)
        if self.db_loaded():
            try:
                assert isinstance(self.db, Database)
                self.db.tag_table_export(file_name)
            except Exception as e:
                return self.resp.exception(f'Cannot export tag table', e)
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
        trace('field_table_list')
        if self.db_loaded():
            try:
                assert isinstance(self.db, Database)
                return self.resp.ok(self.db.sql.get_field_table_list())
            except Exception as e:
                return self.resp.exception('cannot list field table', e)
        else:
            return self.resp.warning(NO_DATABASE)

    def field_table_count(self) -> Response:
        """
        Print field count (or how many there are)
        :return: response
        """
        trace('field_table_count')
        if self.db_loaded():
            try:
                assert isinstance(self.db, Database)
                return self.resp.ok(self.db.sql.get_table_count(NAME_FIELD_TABLE))
            except Exception as e:
                return self.resp.exception('cannot return field table count', e)
        else:
            return self.resp.warning(NO_DATABASE)

    def field_table_search(self, pattern: str) -> Response:
        """
        Search for fields matching a pattern
        :param pattern: regexp pattern
        :return: response
        """
        trace('field_table_search', pattern)
        if self.db_loaded():
            try:
                assert isinstance(self.db, Database)
                return self.resp.ok(self.db.sql.search_field_table(pattern))
            except Exception as e:
                return self.resp.exception('cannot search field table', e)
        else:
            return self.resp.warning(NO_DATABASE)

    def field_table_add(self, name: str, sensitive_flag: bool) -> Response:
        """
        Add new field to the field table
        :param name: field name
        :param sensitive_flag: sensitive?
        :return: response
        """
        trace('field_table_add', name, sensitive_flag)
        if self.db_loaded():
            try:
                assert isinstance(self.db, Database)
                field_mapping = self.db.sql.get_field_table_name_mapping()
                if name in field_mapping:
                    return self.resp.error(f'field {name} already exists')
                else:
                    f_id = self.db.sql.insert_into_field_table(None, name, sensitive_flag)
                    return self.resp.ok(f'Added field {name} with id {f_id}')
            except Exception as e:
                return self.resp.exception('cannot add field to table', e)
        else:
            return self.resp.warning(NO_DATABASE)

    def field_table_rename(self, old_name: str, new_name: str) -> Response:
        """
        Rename existing tag
        :param old_name: old field name
        :param new_name: new field name
        :return: response
        """
        trace('field_table_rename', old_name, new_name)
        if self.db_loaded():
            try:
                assert isinstance(self.db, Database)
                if self.db.sql.rename_field_table_entry(old_name, new_name) == 0:
                    return self.resp.error(f'cannot rename field {old_name}')
                else:
                    return self.resp.ok(f'field {old_name} -> {new_name}')
            except Exception as e:
                return self.resp.exception('cannot rename field in table', e)
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
            try:
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
            except Exception as e:
                return self.resp.exception('cannot delete field from table', e)
        else:
            return self.resp.warning(NO_DATABASE)

    def field_table_import(self, file_name: str):
        """
        TODO
        Import fields from a csv file
        :param file_name: output file name
        :return: response
        """
        trace('field_table_import', file_name)
        if self.db_loaded():
            try:
                assert isinstance(self.db, Database)
                if self.db.sql.get_table_count(NAME_FIELD_TABLE) == 0:
                    self.db.field_table_import(file_name)
                    return self.resp.ok(f'imported {self.db.sql.get_table_count(NAME_FIELD_TABLE)} fields')
                else:
                    return self.resp.error('database already has fields defined')
            except Exception as e:
                return self.resp.exception('cannot import field table', e)
        else:
            return self.resp.warning(NO_DATABASE)

    def field_table_export(self, file_name: str):
        """
        Export fields into csv file
        :param file_name: output file name
        :return: response
        """
        trace('field_table_export', file_name)
        if self.db_loaded():
            try:
                assert isinstance(self.db, Database)
                self.db.field_table_export(file_name)
            except Exception as e:
                return self.resp.exception(f'Cannot export field table', e)
        else:
            return self.resp.warning(NO_DATABASE)

    # -----------------------------------------------------------------
    # Tags commands
    # -----------------------------------------------------------------

    def tag_add(self, item_id: int, tag_name: str) -> Response:
        """
        Add tag to item
        :param item_id: item id
        :param tag_name: tag name
        :return:
        """
        trace('tag_add', item_id, tag_name)
        if self.db_loaded():
            try:
                tag_mapping = self.db.sql.get_tag_table_name_mapping()
                if tag_name in tag_mapping:
                    tag_id = tag_mapping[tag_name][INDEX_ID]
                    if self.db.sql.tag_exists(item_id, tag_id):
                        return self.resp.error(f'tag {tag_name} already exists in item')
                    n = self.db.sql.insert_into_tags(None, item_id, tag_id)
                    return self.resp.ok(f'added {tag_name} to item {item_id} with id={n}')
                else:
                    return self.resp.error(f'tag {tag_name} does not exist')
            except Exception as e:
                return self.resp.exception('cannot add tag to item', e)
        else:
            return self.resp.warning(NO_DATABASE)

    def tag_delete(self, item_id: int, tag_name: str) -> Response:
        """
        Delete tag from item
        :param item_id: item id
        :param tag_name: tag name
        :return: response
        """
        trace('tag_delete', item_id, tag_name)
        if self.db_loaded():
            try:
                tag_mapping = self.db.sql.get_tag_table_name_mapping()
                if tag_name in tag_mapping:
                    tag_id = tag_mapping[tag_name][MAP_TAG_ID]
                    if self.db.sql.tag_exists(item_id, tag_id):
                        n = self.db.sql.delete_from_tags(item_id, tag_id)
                        return self.resp.ok(f'deleted {tag_name} from item {item_id}, {n} tags deleted')
                    else:
                        return self.resp.error(f'tag {tag_name} does not exist in item')
                else:
                    return self.resp.error(f'tag {tag_name} does not exist')
            except Exception as e:
                return self.resp.exception('cannot delete tag from item', e)
        else:
            return self.resp.warning(NO_DATABASE)

    # -----------------------------------------------------------------
    # Field commands
    # -----------------------------------------------------------------

    def field_add(self, item_id: int, field_name: str, field_value: str) -> Response:
        """
        :param item_id: item id
        :param field_name: field name
        :param field_value: field value
        :return: response
        """
        trace('field_add', item_id, field_name, field_value)
        if self.db_loaded():
            try:
                field_mapping = self.db.sql.get_field_table_name_mapping()
                if field_name in field_mapping:
                    field_table_id = field_mapping[field_name][MAP_FIELD_ID]
                    f_sensitive = field_mapping[field_name][MAP_FIELD_SENSITIVE]
                    f_value = self.encrypt_value(field_value) if f_sensitive else field_value
                    trace('field_add', field_table_id, field_value)
                    n = self.db.sql.insert_into_fields(None, item_id, field_table_id, f_value, f_value != field_value)
                    return self.resp.ok(f'added {field_name} to item {item_id} with id={n}')
                else:
                    return self.resp.error(f'field {field_name} does not exist')
            except Exception as e:
                return self.resp.exception('cannot add field to item', e)
        else:
            return self.resp.warning(NO_DATABASE)

    def field_delete(self, item_id: int, field_id: int) -> Response:
        """
        :param item_id: item id
        :param field_id: field id
        :return: response
        """
        trace('field_delete', item_id, field_id)
        if self.db_loaded():
            try:
                if self.db.sql.field_exists(item_id, field_id):
                    n = self.db.sql.delete_from_fields(item_id, field_id)
                    return self.resp.ok(f'deleted {field_id} from item {item_id}, {n} fields deleted')
                else:
                    return self.resp.error(f'field {field_id} does not exist')
            except Exception as e:
                return self.resp.exception('cannot delete field from item', e)
        else:
            return self.resp.warning(NO_DATABASE)

    # def get_name(self, f_id: int | None) -> str:
    #     f_mapping = self.db.sql.get_field_table_id_mapping()
    #     return f_mapping[f_id][MAP_FIELD_NAME] if f_id in f_mapping else '???'

    def field_update(self, item_id: int, field_id: int, new_field_name: str | None,
                     new_field_value: str | None) -> Response:
        """
        :param item_id: item id
        :param field_id: field id
        :param new_field_name: field name
        :param new_field_value: field value
        :return: response
        """
        trace('field_update', item_id, field_id, new_field_name, new_field_value)
        if self.db_loaded():
            try:
                if new_field_name is None and new_field_value is None:
                    return self.resp.warning('nothing to update')

                if self.db.sql.field_exists(item_id, field_id):

                    # Get existing field attributes
                    field = self.db.sql.field_get(field_id)[0]
                    f_id = field[INDEX_FIELDS_FIELD_ID]
                    f_value = field[INDEX_FIELDS_VALUE]
                    f_encrypted = bool(field[INDEX_FIELDS_ENCRYPTED])
                    field_mapping = self.db.sql.get_field_table_id_mapping()
                    f_sensitive = field_mapping[f_id][MAP_FIELD_SENSITIVE]

                    # The field table id and sensible flag will be set by the new field name if defined.
                    # Otherwise the sensible flag will be inherited from the current field.
                    if new_field_name is not None:
                        field_mapping = self.db.sql.get_field_table_name_mapping()
                        if new_field_name in field_mapping:
                            field_table_id = field_mapping[new_field_name][MAP_FIELD_ID]
                            new_sensitive = field_mapping[new_field_name][MAP_FIELD_SENSITIVE]
                        else:
                            return self.resp.error(f'field name {new_field_name} does not exist')
                    else:
                        field_table_id = f_id
                        new_sensitive = f_sensitive

                    # Decide whether the value needs to be encrypted, decrypted or left untouched.
                    new_value = f_value
                    encrypted_flag = False
                    if new_field_value is not None:
                        new_value = self.encrypt_value(new_field_value) if new_sensitive else new_field_value
                        encrypted_flag = new_value != new_field_value
                    else:
                        if f_encrypted and not new_sensitive:
                            new_value = self.decrypt_value(f_value)
                        elif not f_encrypted and new_sensitive:
                            new_value = self.encrypt_value(f_value)
                            encrypted_flag = new_value != f_value
                        elif f_encrypted and new_sensitive:
                            encrypted_flag = True
                    n = self.db.sql.update_field(item_id, field_id, field_table_id, new_value, encrypted_flag)
                    if n > 0:
                        return self.resp.ok(f'updated {n} fields')
                    else:
                        return self.resp.warning('no fields updated')
                else:
                    return self.resp.error(f'field {field_id} does not exist')
            except Exception as e:
                return self.resp.exception('cannot update item field', e)
        else:
            return self.resp.warning(NO_DATABASE)

    # -----------------------------------------------------------------
    # Item commands
    # -----------------------------------------------------------------

    # def item_exists(self, item_id: int) -> Response:
    #     """
    #     Check whether the item exists in the database
    #     :param item_id: item id
    #     :return: True if it exists, False otherwise
    #     """
    #     if self.db_loaded():
    #         return self.resp.ok(self.db.sql.item_exists(item_id))
    #     else:
    #         return self.resp.warning(NO_DATABASE)

    def item_list(self) -> Response:
        """
        List all items
        """
        trace('item_list')
        if self.db_loaded():
            try:
                assert isinstance(self.db, Database)
                return self.resp.ok(self.db.sql.get_item_list())
            except Exception as e:
                return self.resp.exception('cannot list items', e)
        else:
            return self.resp.warning(NO_DATABASE)

    def item_count(self) -> Response:
        """
        Print the number of items
        :return:
        """
        trace('item_count')
        if self.db_loaded():
            try:
                assert isinstance(self.db, Database)
                return self.resp.ok(self.db.sql.get_table_count(NAME_ITEMS))
            except Exception as e:
                return self.resp.exception('cannot return item count', e)
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
            try:
                assert isinstance(self.db, Database)
                item_list = self.db.search(pattern, item_name_flag=name_flag, tag_flag=tag_flag,
                                           field_name_flag=field_name_flag, field_value_flag=field_value_flag,
                                           note_flag=note_flag)
                return self.resp.ok(item_list)
            except Exception as e:
                return self.resp.exception('cannot search items', e)
        else:
            return self.resp.warning(NO_DATABASE)

    def item_get(self, item_id: int) -> Response:
        """
        Get item as a dictionary
        :param item_id: item id
        """
        trace('item_get', item_id)
        if self.db_loaded():
            try:
                assert isinstance(self.db, Database)

                # Get item and field information
                tag_mapping = self.db.sql.get_tag_table_id_mapping()
                field_mapping = self.db.sql.get_field_table_id_mapping()
                tag_list = self.db.sql.get_tag_list(item_id=item_id)
                field_list = self.db.sql.get_field_list(item_id=item_id)
                item_list = self.db.sql.get_item_list(item_id=item_id)
                if len(item_list) > 0:
                    item = item_list[0]
                    d = {KEY_DICT_ID: item_id,
                         KEY_DICT_NAME: item[INDEX_ITEMS_NAME],
                         KEY_DICT_TIMESTAMP: item[INDEX_ITEMS_DATE],
                         KEY_DICT_NOTE: item[INDEX_ITEMS_NOTE],
                         KEY_DICT_TAGS: [tag_mapping[t_id][MAP_TAG_NAME] for _, t_id, _ in tag_list],
                         KEY_DICT_FIELDS: [(f_id, field_mapping[field_id][MAP_FIELD_NAME], f_value, f_encrypted)
                                           for f_id, field_id, _, f_value, f_encrypted in field_list],
                         }
                    return self.resp.ok(d)
                else:
                    return self.resp.error(f'item {item_id} does not exist')
            except Exception as e:
                return self.resp.exception('cannot get item', e)
        else:
            return self.resp.warning(NO_DATABASE)

    def item_add(self, item_name: str, tag_list: list, note: str) -> Response:
        """
        Add/create new item
        :param item_name: new items name
        :param tag_list: tag name list
        :param note: note
        """
        trace('item_add', item_name, tag_list, note)
        if self.db_loaded():
            try:
                item_id = self.db.sql.insert_into_items(None, item_name, get_timestamp(), note)
                trace('item_id', item_id)
                if tag_list:
                    tag_mapping = self.db.sql.get_tag_table_name_mapping()
                    for tag_name in tag_list:
                        tag_id = tag_mapping[tag_name][MAP_TAG_ID]
                        trace('adding tag', tag_name, tag_id)
                        self.db.sql.insert_into_tags(None, item_id, tag_id)
                return self.resp.ok(item_id)
            except Exception as e:
                return self.resp.exception('cannot get item', e)
        else:
            return self.resp.warning(NO_DATABASE)

    def item_delete(self, item_id: int) -> Response:
        """
        Delete item
        :param item_id: item id
        """
        trace(f'item_delete {item_id}')
        if self.db_loaded():
            try:
                assert isinstance(self.db, Database)
                n_tags = self.db.sql.delete_from_tags(item_id)
                n_fields = self.db.sql.delete_from_fields(item_id)
                if self.db.sql.delete_from_items(item_id) > 0:
                    # self.db.sql.update_counters()
                    return self.resp.ok(f'removed item {item_id}: {n_tags} tags and {n_fields} fields')
                else:
                    return self.resp.error(f'Item {item_id} does not exist: {n_tags} tags, {n_fields} fields')
            except Exception as e:
                return self.resp.exception('cannot delete item', e)
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
            try:
                assert isinstance(self.db, Database)
                item_list = self.db.sql.get_item_list(item_id=item_id)
                tag_list = self.db.sql.get_tag_list(item_id=item_id)
                field_list = self.db.sql.get_field_list(item_id=item_id)
                if len(item_list) > 0:
                    _, i_name, _, i_note = item_list[0]
                    new_item_id = self.db.sql.insert_into_items(None, 'Copy of ' + i_name, get_timestamp(), i_note)
                    for _, t_id, _ in tag_list:
                        self.db.sql.insert_into_tags(None, t_id, new_item_id)
                    for _, f_id, _, f_value, f_encrypted in field_list:
                        self.db.sql.insert_into_fields(None, f_id, new_item_id, f_value, f_encrypted)
                    return self.resp.ok(f'added item {new_item_id}, {len(tag_list)} tags, {len(field_list)} fields')
                else:
                    return self.resp.error(f'item {item_id} does not exist')
            except Exception as e:
                return self.resp.exception('cannot copy item', e)
        else:
            return self.resp.warning(NO_DATABASE)

    def item_update(self, item_id: int, item_name: str | None, note: str | None) -> Response:
        """
        Update item contents
        :param item_id: item id
        :param item_name: item name
        :param note: item note
        """
        trace('item_update', item_id, item_name, note)
        if self.db_loaded():
            try:
                if item_name is not None or note is not None:
                    n = self.db.sql.update_item(item_id, get_timestamp(), item_name=item_name, item_note=note)
                    return self.resp.ok(f'updated {n} item') if n > 0 else self.resp.warning('no items updated')
                else:
                    return self.resp.warning('nothing to update')
            except Exception as e:
                return self.resp.exception('cannot update item', e)
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
