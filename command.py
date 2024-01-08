import re
from enum import Enum, auto
from os.path import exists
from typing import Optional
from db import Database, DEFAULT_DATABASE_NAME
from sql import NAME_TAG_TABLE, NAME_FIELD_TABLE, NAME_TAGS, NAME_FIELDS, NAME_ITEMS
from sql import INDEX_ID, INDEX_NAME, INDEX_COUNT
from utils import get_password, get_timestamp, timestamp_to_string, print_line, sensitive_mark, error, confirm, trace


class ExportFormat(Enum):
    FORMAT_JSON = auto()
    FORMAT_SQL = auto()


class CommandProcessor:

    def __init__(self):
        """
        The command processor handles the commands that interact with the database
        """
        self.file_name = ''  # database file name
        self.db = None  # database object

    def db_loaded(self, overwrite=False) -> bool:
        """
        Check whether there's a database in memory
        Prompt the user whether to overwrite the database if there is one already
        :return: True if there's a database and the database can be overwritten, False otherwise
        """
        if self.db is None:
            return False
        elif overwrite:
            if confirm("There's a database already in memory that will be overwritten"):
                return True
            else:
                return False
        else:
            return True

    # -----------------------------------------------------------------
    # Database commands
    # -----------------------------------------------------------------

    def database_create(self, file_name=DEFAULT_DATABASE_NAME):
        """
        Create an empty database
        :param file_name: database file name
        """
        trace('database_create', file_name)
        if self.db_loaded(overwrite=True):
            return

        # Check whether the file exists already.
        # Create an empty database if that's not the case.
        if exists(file_name):
            error(f'database {file_name} already exists')
        else:
            self.file_name = file_name
            self.db = Database(file_name, get_password())

    def database_read(self, file_name: str):
        """
        Read database into memory
        :param file_name: database file name
        :return:
        """
        trace('database_read', file_name)
        if self.db_loaded(overwrite=True):
            return
        print(f'Reading from {file_name}')
        try:
            self.db = Database(file_name, get_password())
            self.db.read()
            self.file_name = file_name
        except Exception as e:
            error(f'failed to read database {file_name}', e)
            self.db = None
            self.file_name = DEFAULT_DATABASE_NAME

    def database_write(self):
        trace('database_write')
        if self.db_loaded():
            assert isinstance(self.db, Database)
            print(f'Writing to {self.file_name}')
            try:
                self.db.write()
            except Exception as e:
                error('cannot write database', e)

    def database_export(self, file_name: str, output_format: ExportFormat):
        trace('database_export', file_name)
        if self.db_loaded():
            assert isinstance(self.db, Database)
            try:
                if output_format == ExportFormat.FORMAT_JSON:
                    self.db.export_to_json(file_name)
                else:
                    self.db.sql.export_to_sql(file_name)
            except Exception as e:
                error('cannot export database', e)

    def database_dump(self):
        """
        Dump database contents to the terminal
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
        Print a database report
        """
        if self.db_loaded():
            assert isinstance(self.db, Database)
            self.db.database_report()

    # -----------------------------------------------------------------
    # Tag commands
    # -----------------------------------------------------------------

    @staticmethod
    def _format_tag(tag_id: int, tag_name: str, tag_count: int) -> str:
        return f'{tag_id:2d} {tag_count:3d} {tag_name}'

    def tag_list(self):
        """
        List all tags
        """
        if self.db_loaded():
            assert isinstance(self.db, Database)
            for t_id, t_name, t_count in self.db.sql.get_tag_table_list():
                print(self._format_tag(t_id, t_name, t_count))

    def tag_count(self):
        """
        Print tag count (or how many there are)
        """
        if self.db_loaded():
            assert isinstance(self.db, Database)
            print(self.db.sql.get_table_count(NAME_TAG_TABLE))

    def tag_search(self, pattern: str):
        """
        Search for tags matching a pattern
        :param pattern: regexp pattern
        """
        trace('tag_search', pattern)
        if self.db_loaded():
            assert isinstance(self.db, Database)
            for t_id, t_name, t_count in self.db.sql.search_tag_table(pattern):
                print(self._format_tag(t_id, t_name, t_count))

    def tag_add(self, name: str):
        """
        Add new tag
        :param name:
        :return:
        """
        if self.db_loaded():
            assert isinstance(self.db, Database)
            tag_mapping = self.db.sql.get_tag_table_name_mapping()
            if name in tag_mapping:
                error(f'tag {name} already exists')
            else:
                t_id = self.db.sql.insert_into_tag_table(None, name)
                print(f'Added tag {name} with id {t_id}')

    def tag_rename(self, old_name: str, new_name: str):
        """
        Rename existing tag
        :param old_name: old tag name
        :param new_name: new tag name
        :return:
        """
        if self.db_loaded():
            assert isinstance(self.db, Database)
            if self.db.sql.rename_tag_table_entry(old_name, new_name) == 0:
                error(f'cannot rename tag {old_name}')

    def tag_delete(self, name: str):
        """
        Delete tag
        :param name: tag name
        :return:
        """
        if self.db_loaded():
            assert isinstance(self.db, Database)
            self.db.sql.update_counters()
            tag_mapping = self.db.sql.get_tag_table_name_mapping()
            if name in tag_mapping:
                if tag_mapping[name][INDEX_COUNT] == 0:
                    n = self.db.sql.delete_from_tag_table(name)
                    print(f'removed {n} tags')
                else:
                    error(f'tag {name} is being used')
            else:
                error(f'tag {name} does not exist')

    # -----------------------------------------------------------------
    # Field commands
    # -----------------------------------------------------------------

    @staticmethod
    def _format_field(field_id: int, field_name: str, field_sensitive: bool, field_count: int) -> str:
        return f'{field_id:3d} {field_count:4d} {sensitive_mark(field_sensitive)} {field_name}'

    def field_list(self):
        """
        List all fields
        """
        trace('field_list')
        if self.db_loaded():
            assert isinstance(self.db, Database)
            for f_id, f_name, f_sensitive, f_count in self.db.sql.get_field_table_list():
                print(self._format_field(f_id, f_name, f_sensitive, f_count))

    def field_count(self):
        """
        Print field count (or how many there are)
        """
        trace('field_count')
        if self.db_loaded():
            assert isinstance(self.db, Database)
            print(self.db.sql.get_table_count(NAME_FIELD_TABLE))

    def field_search(self, pattern: str):
        """
        Search for fields matching a pattern
        :param pattern: regexp pattern
        """
        trace('field_search', pattern)
        if self.db_loaded():
            assert isinstance(self.db, Database)
            trace('field_search', pattern)
            if self.db_loaded():
                assert isinstance(self.db, Database)
                for f_id, f_name, f_sensitive, f_count in self.db.sql.search_field_table(pattern):
                    print(self._format_field(f_id, f_name, f_sensitive, f_count))

    def field_add(self, name: str, sensitive_flag: bool):
        """
        Add new field
        :param name: field name
        :param sensitive_flag: sensitive?
        :return:
        """
        trace('field_add', name, sensitive_flag)
        if self.db_loaded():
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
        if self.db_loaded():
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
        if self.db_loaded():
            assert isinstance(self.db, Database)
            field_mapping = self.db.sql.get_field_table_name_mapping()
            if name in field_mapping:
                if field_mapping[name][INDEX_COUNT] == 0:
                    n = self.db.sql.delete_from_field_table(name)
                    print(f'removed {n} fields')
                else:
                    error(f'field {name} is being used')
            else:
                error(f'field {name} does not exist')

    # -----------------------------------------------------------------
    # Item commands
    # -----------------------------------------------------------------

    def item_list(self):
        """
        List all items

        """
        trace('item_list')
        if self.db_loaded():
            assert isinstance(self.db, Database)
            for t_uid, t_name, item_timestamp, _ in self.db.sql.get_item_list():
                print(f'{t_uid:5d}  {timestamp_to_string(item_timestamp, date_only=True)}  {t_name}')

    def item_print(self, item_id: int, show_sensitive: bool):
        """
        Print item
        :param item_id: item uid
        :param show_sensitive: print sensitive fields unencrypted
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

            # Iterate over the list of items (it should be just one)
            if len(item_list) > 0:
                for i_id, i_name, i_timestamp, i_note in item_list:
                    print(f'id:    {i_id}')
                    print(f'name:  {i_name}')
                    print(f'date:  {timestamp_to_string(i_timestamp)}')
                    print(f'tags:  {[tag_mapping[t_id][INDEX_NAME] for _, t_id, _ in tag_list]}')
                    print('fields:')
                    for f_id, field_id, _, f_value, f_encrypted in field_list:
                        f_name = field_mapping[field_id][INDEX_NAME]
                        print(f'  {f_id:4d} {sensitive_mark(f_encrypted)} {f_name} {f_value}')
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
        if self.db_loaded():
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
        if self.db_loaded():
            assert isinstance(self.db, Database)
            # TODO
            # item_list = self.db.search(pattern, item_name_flag=name_flag, tag_flag=tag_flag,
            #                            field_name_flag=field_name_flag, field_value_flag=field_value_flag,
            #                            note_flag=note_flag)
            # for item in item_list:
            #     assert isinstance(item, Item)
            #     print(f'{item.get_id()} - {item.name}')

    def item_delete(self, uid: int):
        """
        Delete item
        :param uid: item uid
        """
        trace(f'item_delete {uid}')
        if self.db_loaded():
            assert isinstance(self.db, Database)
            # try:
            #     self.db.item_collection.remove(uid)
            # except Exception as e:
            #     error('error while removing item', e)

    def item_create(self, item_name: str, tag_list: list, field_list, note: str, multiline_note: bool):
        """
        Create new item
        :param item_name:
        :param tag_list:
        :param field_list:
        :param note:
        :param multiline_note:
        """
        trace('item_create')
        if self.db_loaded():
            assert isinstance(self.db, Database)
            # TODO
            # # Make sure the name is specified
            # if not item_name:
            #     error('item name is required')
            #     return
            #
            # # Process tags
            # try:
            #     tag_uid_list = self.db.tag_table.get_tag_uid_list(tag_list)
            # except Exception as e:
            #     error(f'Error while processing tag list', e)
            #     return
            # trace(f'tag uid list {tag_uid_list}')
            #
            # # Process fields
            # fc = FieldCollection()
            # f_name = ''
            # try:
            #     for f_name, f_value in field_list:
            #         fc.add(Field(f_name, f_value, self.db.field_table.is_sensitive(name=f_name)))
            # except Exception as e:
            #     error(f'Error while adding field {f_name}', e)
            #     return
            # trace('field collection', fc)
            #
            # try:
            #     item = Item(item_name, tag_uid_list, note, fc, time_stamp=get_timestamp())
            #     # item.dump()
            #     self.db.item_collection.add(item)
            #     print(f'Added item {item.get_id()}')
            # except Exception as e:
            #     error(f'Error while adding item {item_name}', e)

    def item_add(self, uid: int, item_name: str, tag_list: list,
                 field_list: list, note: str, multiline_note: bool):
        """
        Add item
        :param uid: item uid
        :param item_name: item name
        :param tag_list: tag list
        :param field_list: list of tuples with the field,value pairs to add/edit
        :param note: item note
        :param multiline_note: multiline note?
        """
        self.item_add_edit(uid, item_name, tag_list, field_list, [], note, multiline_note, add_flag=True)

    def item_edit(self, uid: int, item_name: str, tag_list: list,
                  field_list: list[tuple], field_delete_list: list,
                  note: str, multiline_note: bool):
        """
        Edit item
        :param uid: item uid
        :param item_name: item name
        :param tag_list: tag list
        :param field_list: list of tuples with the field,value pairs to add/edit
        :param field_delete_list: list of field names to delete
        :param note: item note
        :param multiline_note: multiline note?
        """
        self.item_add_edit(uid, item_name, tag_list, field_list, field_delete_list, note, multiline_note)

    def item_add_edit(self, uid: int, item_name: str, tag_list: list,
                      field_list: list, field_delete_list: list,
                      note: str, multiline_note: bool,
                      add_flag: Optional[bool] = False):
        """
        Edit existing item
        :param uid: item uid
        :param item_name: item name
        :param tag_list: tag list
        :param field_list: list of tuples with the field,value pairs to add/edit
        :param field_delete_list: list of field names to delete
        :param note: item note
        :param multiline_note: multiline note?
        :param add_flag: allow adding items? (used for tags only)
        """
        trace('item_edit', uid)
        if self.db_loaded():
            assert isinstance(self.db, Database)
            # TODO
            # try:
            #     item = self.db.item_collection.get(uid)
            #     assert isinstance(item, Item)
            # except Exception as e:
            #     error(f'item {uid} does not exist', e)
            #     return
            #
            # # Set new name and note
            # new_name = item_name if item_name else item.get_name()
            # new_note = note if note else item.get_note()
            # trace(f'new name={new_name}, note={new_note}')
            #
            # # Process tags
            # if tag_list:
            #     try:
            #         tag_uid_list = self.db.tag_table.get_tag_uid_list(tag_list)
            #         if add_flag:
            #             new_tag_list = list(set(tag_uid_list + item.get_tags()))
            #         else:
            #             new_tag_list = tag_uid_list
            #     except Exception as e:
            #         error(f'Error while processing tag list', e)
            #         return
            # else:
            #     new_tag_list = item.get_tags()
            # trace(f'new tag list {new_tag_list}')
            #
            # # Process fields
            # field_dict = {k: v for k, v in field_list}
            # trace('field_dict', field_dict)
            # fc = FieldCollection()
            # try:
            #     # Iterate over all the fields in the existing item
            #     for field in item.next_field():
            #         assert isinstance(field, Field)
            #         f_name, f_value, f_sensitive = field.get_name(), field.get_value(), field.get_sensitive()
            #
            #         # Skip fields that should be deleted
            #         if f_name in field_delete_list:
            #             trace('skipped', f_name)
            #             continue
            #
            #         # Add fields to the new field collection
            #         # Use the (new) value from the field_ dict if the field is there
            #         # Otherwise keep the old value
            #         trace('existing field', f_name, f_value, f_sensitive)
            #         if f_name in field_dict:
            #             fc.add(Field(f_name, field_dict[f_name], f_sensitive))
            #             trace(f'field value for {f_name} updated from {f_value} to {field_dict[f_name]}')
            #             del field_dict[f_name]  # remove used field
            #         else:
            #             trace(f'field value for {f_name} preserved {f_value}')
            #             fc.add(Field(f_name, f_value, f_sensitive))
            #
            #     # Add any fields in the field_dict that were not processed already
            #     # This will done regardless of the value of the add flag
            #     for f_name in field_dict:
            #         f_sensitive = self.db.field_table.is_sensitive(name=f_name)
            #         trace(f'adding new field {f_name} {field_dict[f_name]}, {f_sensitive}')
            #         fc.add(Field(f_name, field_dict[f_name], f_sensitive))
            #
            # except Exception as e:
            #     print(e)
            #
            # # Create the new item
            # try:
            #     new_item = Item(new_name, new_tag_list, new_note, fc, time_stamp=get_timestamp(), uid=item.get_id())
            #     new_item.dump()
            #     self.db.item_collection.update(new_item)
            # except Exception as e:
            #     error('error when creating item', e)
            #     return

    def item_copy(self, uid: int):
        """
        Create a copy of an item with a different uid
        The field collection is recreated and the timestamp updated.
        :param uid: item uid
        """
        trace('item_copy', uid)
        if self.db_loaded():
            assert isinstance(self.db, Database)
            # TODO
            # try:
            #     item = self.db.item_collection.get(uid)
            #     assert isinstance(item, Item)
            #     fc = FieldCollection()
            #     for field in item.field_collection.next():
            #         assert isinstance(field, Field)
            #         f_name, f_value, f_sensitive = field.get_name(), field.get_value(), field.get_sensitive()
            #         fc.add(Field(f_name, f_value, f_sensitive))
            #     new_item = Item('Copy of ' + item.get_name(), item.get_tags(), item.get_note(), fc,
            #                     uid=ItemUid.get_uid())
            #     trace('new item', new_item)
            #     self.db.item_collection.add(new_item)
            #     print(f'create item {new_item.get_id()} from {item.get_id()}')
            # except Exception as e:
            #     print('cannot make copy of item', e)

    # def item_dump(self, uid: int):
    #     """
    #     Dump item contents
    #     :param uid: item uid
    #     """
    #     trace('item_dump', uid)
    #     if self.db_loaded():
    #         assert isinstance(self.db, Database)
    #         # TODO
    #         # if uid in self.db.item_collection:
    #         #     item = self.db.item_collection.get(uid)
    #         #     assert isinstance(item, Item)
    #         #     print_line()
    #         #     item.dump()
    #         #     print_line()
    #         # else:
    #         #     error(f'item {uid} not found')

    # -----------------------------------------------------------------
    # Misc commands
    # -----------------------------------------------------------------

    def quit_command(self, keyboard_interrupt: bool):
        """
        Command that will be called when the program exits
        """
        trace(f'quit_command {self.file_name}', keyboard_interrupt)


if __name__ == '__main__':
    cp = CommandProcessor()
    cp.database_read(DEFAULT_DATABASE_NAME)
    cp.item_list()
    cp.item_dump(2710)
