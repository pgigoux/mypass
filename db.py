import os
import re
import json
from sql import Sql, TABLE_LIST
from sql import MAP_TAG_ID, MAP_TAG_NAME
from sql import MAP_FIELD_ID, MAP_FIELD_NAME, MAP_FIELD_SENSITIVE
from crypt import Crypt
from utils import trace, filter_control_characters, timestamp_to_string, get_string_timestamp, print_line

# Keywords used to export the database to json
# common
KEY_ID = 'uid'
KEY_NAME = 'name'
KEY_COUNT = 'count'
# main sections
KEY_TAG_SECTION = 'tags'
KEY_FIELD_SECTION = 'fields'
KEY_ITEM_SECTION = 'items'
# field table
KEY_SENSITIVE = 'sensitive'
# items
KEY_TIMESTAMP = 'timestamp'
KEY_NOTE = 'note'
KEY_TAGS = 'tags'
KEY_FIELDS = 'fields'
# fields
KEY_VALUE = 'value'
KEY_ENCRYPTED = 'encrypted'

DEFAULT_DATABASE_NAME = 'pw.db'

# Temporary file used when saving database
TEMP_FILE = 'db.tmp'


class Database:

    def __init__(self, file_name: str, crypt_key: Crypt | None):
        """
        :param file_name: database file name
        :param crypt_key: key to encode/decode data
        """
        self.sql = Sql()
        self.file_name = file_name
        # The database will be encrypted if the key is not None
        self.crypt_key = crypt_key
        self.checksum = self.calculate_checksum()

    def __str__(self) -> str:
        return f'file={self.file_name}, sql={str(self.sql)} crypt={str(self.crypt_key)}'

    def read_mode(self) -> str:
        """
        Return the file write mode depending on whether encryption is enabled
        :return: write mode
        """
        return 'r' if self.crypt_key is None else 'rb'

    def write_mode(self) -> str:
        """
        Return the file write mode depending on whether encryption is enabled
        :return: write mode
        """
        return 'w' if self.crypt_key is None else 'wb'

    def get_checksum(self):
        return self.checksum

    def calculate_checksum(self) -> str:
        """
        Calculate the database checksum
        :return: string containing the checksum
        """
        return self.sql.get_checksum()

    def update_checksum(self):
        """
        Update the database checksum
        """
        self.checksum = self.calculate_checksum()

    def _tag_table_to_list(self) -> list:
        """
        Return the tag_table as a list of where each element is a dictionary
        containing the tag id, tag name and count.
        :return: list of tags
        """
        output_list = []
        for tag_id, t_name, t_count in self.sql.get_tag_table_list():
            output_list.append({KEY_ID: tag_id, KEY_NAME: t_name, KEY_COUNT: t_count})
        return output_list

    def _field_table_to_list(self) -> list:
        """
        Return the tag_table as a list of where each element is a dictionary
        containing the tag id, tag name and count.
        :return: list of fields
        """
        output_list = []
        for f_id, f_name, f_sensitive, f_count in self.sql.get_field_table_list():
            output_list.append({KEY_ID: f_id, KEY_NAME: f_name, KEY_SENSITIVE: bool(f_sensitive), KEY_COUNT: f_count})
        return output_list

    def _items_to_dict(self, decrypt_flag=False) -> dict:
        """
        Convert the items in the database into a dictionary. Aside from the fixed
        item attributes (name, timestamp, note), the dictionary also contains the
        list of tags and a dictionary with the field information.
        :param decrypt_flag: decrypt field values if encryption is enabled?
        :return: dictionary with items
        """
        output_dict = {}

        # Get the tag and field mappings to convert ids into names
        tag_mapping = self.sql.get_tag_table_id_mapping()
        field_mapping = self.sql.get_field_table_id_mapping()

        # Query the database to get all items
        item_fetch_list = self.sql.get_item_list()

        # Iterate over all items
        for item_id, item_name, item_date, item_note in item_fetch_list:
            # Item fixed attributes
            item_dict = {KEY_NAME: item_name, KEY_TIMESTAMP: item_date, KEY_NOTE: item_note}

            # Process the item tags
            tag_fetch_list = self.sql.get_tag_list(item_id=item_id)
            item_dict[KEY_TAGS] = [tag_mapping[tag_id][MAP_TAG_NAME] for _, tag_id, _ in tag_fetch_list]

            # Process the item fields
            field_fetch_list = self.sql.get_field_list(item_id=item_id)
            field_dict = {}
            for field_id, f_id, _, field_value, f_encrypted in field_fetch_list:
                if decrypt_flag and f_encrypted and self.crypt_key is not None:
                    field_value = self.crypt_key.decrypt_str2str(field_value)
                    f_encrypted = False
                tmp_dict = {KEY_NAME: field_mapping[f_id][MAP_FIELD_NAME], KEY_VALUE: field_value,
                            KEY_ENCRYPTED: bool(f_encrypted)}
                field_dict[field_id] = tmp_dict
            item_dict[KEY_FIELDS] = field_dict

            output_dict[item_id] = item_dict

        return output_dict

    def sql_to_json(self, decrypt_flag=False) -> str:
        """
        Convert the database to a json format string
        :param decrypt_flag: decrypt item fields?
        :return: json string
        """
        d = {KEY_TAG_SECTION: self._tag_table_to_list(),
             KEY_FIELD_SECTION: self._field_table_to_list(),
             KEY_ITEM_SECTION: self._items_to_dict(decrypt_flag=decrypt_flag)}
        return json.dumps(d)

    def json_to_sql(self, data: str, encrypt_flag=False):
        """
        Convert data in json format into a database
        :param encrypt_flag: encrypt fields?
        :param data: json data
        """
        try:
            json_data = json.loads(data)
        except Exception as e:
            raise ValueError(f'failed to convert to json: {repr(e)}')

        # Read the tag table
        try:
            for tag in json_data[KEY_TAG_SECTION]:
                self.sql.insert_into_tag_table(int(tag[KEY_ID]), tag[KEY_NAME], tag[KEY_COUNT])
        except Exception as e:
            raise ValueError(f'failed to read the tag table: {repr(e)}')

        # Read the field table
        try:
            for field in json_data[KEY_FIELD_SECTION]:
                self.sql.insert_into_field_table(int(field[KEY_ID]), field[KEY_NAME],
                                                 bool(field[KEY_SENSITIVE]), field[KEY_COUNT])
        except Exception as e:
            # self.clear()
            raise ValueError(f'failed to read the field table: {repr(e)}')

        # Read items
        tag_mapping = self.sql.get_tag_table_name_mapping()
        field_mapping = self.sql.get_field_table_name_mapping()
        try:
            for item_id in json_data[KEY_ITEM_SECTION]:
                item = json_data[KEY_ITEM_SECTION][item_id]
                self.sql.insert_into_items(None, item[KEY_NAME], int(item[KEY_TIMESTAMP]), item[KEY_NOTE])
                for tag in item[KEY_TAGS]:
                    self.sql.insert_into_tags(None, int(item_id), tag_mapping[tag][MAP_TAG_ID])
                for field_id in item[KEY_FIELDS]:
                    field = item[KEY_FIELDS][field_id]
                    f_name = field[KEY_NAME]
                    f_value = field[KEY_VALUE]
                    f_encrypted = field[KEY_ENCRYPTED]
                    if (encrypt_flag and self.crypt_key is not None and not f_encrypted and
                            field_mapping[f_name][MAP_FIELD_SENSITIVE]):
                        f_value = self.crypt_key.encrypt_str2str(f_value)
                        f_encrypted = True
                    self.sql.insert_into_fields(None, int(item_id), int(field_mapping[f_name][MAP_FIELD_ID]),
                                                f_value, f_encrypted)
        except Exception as e:
            raise ValueError(f'failed to read the items: {repr(e)}')

    def tag_table_import(self, file_name: str):
        """
        Export tag table in csv format
        :param file_name: output file name
        """
        trace(f'db.tag_table_import {file_name}')
        with open(file_name, 'r') as f:
            for line in f:
                tag_id, tag_name = line.strip().split(',')
                self.sql.insert_into_tag_table(int(tag_id), tag_name)
            f.close()

    def tag_table_export(self, file_name: str):
        """
        Export tag table in csv format
        :param file_name: output file name
        """
        trace(f'db.tag_table_export {file_name}')
        with open(file_name, 'w') as f:
            for t_id, t_name, _ in self.sql.get_tag_table_list():
                f.write(f'{t_id},{t_name}\n')
            f.close()

    def field_table_import(self, file_name: str):
        """
        Import field table from csv format
        :param file_name: output file name
        """
        trace(f'db.field_table_import {file_name}')
        with open(file_name, 'r') as f:
            for line in f:
                f_id, f_name, f_sensitive = line.strip().split(',')
                self.sql.insert_into_field_table(int(f_id), f_name, True if int(f_sensitive) == 1 else False)
            f.close()

    def field_table_export(self, file_name: str):
        """
        Export field table in csv format
        :param file_name: output file name
        """
        trace(f'db.field_table_export {file_name}')
        with open(file_name, 'w') as f:
            for f_name, f_uid, f_sensitive, _ in self.sql.get_field_table_list():
                f.write(f'{f_name},{f_uid},{f_sensitive}\n')
            f.close()

    def import_from_json(self, file_name: str):
        """
        Import database from json format.
        The input file should not be encrypted.
        :param file_name: input file name
        """
        with open(file_name, 'r') as f:
            data = f.read()
        self.json_to_sql(data, encrypt_flag=True)

    def export_to_json(self, file_name: str, decrypt_flag=False):
        """
        Export database in json format
        :param file_name: output file name
        :param decrypt_flag: decrypt data before writing
        """
        trace('db.export_to_json', file_name, decrypt_flag)
        with open(file_name, 'w') as f:
            f.write(self.sql_to_json(decrypt_flag=decrypt_flag))
        f.close()

    def search(self, pattern: str, item_name_flag=True, tag_flag=False,
               field_name_flag=False, field_value_flag=False, note_flag=False) -> list:
        """
        Search for items in the database using different matching criteria
        :param pattern: pattern to search for
        :param item_name_flag: search in the item name? (default)
        :param tag_flag: search in the tags?
        :param field_name_flag: search in the field name?
        :param field_value_flag: search in the (unencrypted) field value?
        :param note_flag: search in the note?
        :return: list of items matching the search criteria
        """
        trace(f'db.search', pattern, item_name_flag, tag_flag, field_name_flag, field_value_flag, note_flag)
        output_list = []
        compiled_pattern = re.compile(pattern, flags=re.IGNORECASE)
        tag_mapping = self.sql.get_tag_table_id_mapping()
        field_mapping = self.sql.get_field_table_id_mapping()
        for item_id, item_name, item_timestamp, item_note in self.sql.get_item_list():
            tup = (item_id, item_name, item_timestamp)
            if item_name_flag and compiled_pattern.search(item_name):
                output_list.append(tup)
            if note_flag and compiled_pattern.search(item_note):
                output_list.append(tup)
            if tag_flag:
                tag_list = self.sql.get_tag_list(item_id)
                for _, tag_id, _ in tag_list:
                    if compiled_pattern.search(tag_mapping[tag_id][MAP_TAG_NAME]):
                        output_list.append(tup)
            if field_name_flag or field_value_flag:
                field_list = self.sql.get_field_list(item_id)
                for _, field_id, _, field_value, field_encrypted in field_list:
                    if field_name_flag:
                        if compiled_pattern.search(field_mapping[field_id][MAP_FIELD_NAME]):
                            output_list.append(tup)
                    elif not field_encrypted:
                        if compiled_pattern.search(field_value):
                            output_list.append(tup)
        return output_list

    def read(self):
        """
        Read database from disk. The file name was specified when the database was created.
        """
        trace(f'db.read', self.file_name, self.read_mode())

        # Open and decrypt the input file
        with open(self.file_name, self.read_mode()) as f:
            data = f.read()
            if self.crypt_key is not None:
                assert isinstance(data, bytes)
                try:
                    data = self.crypt_key.decrypt_byte2str(data)
                except Exception as e:
                    raise ValueError(f'failed to decrypt data: {repr(e)}')

        # Read the file contents into the database.
        self.json_to_sql(data)

        # Update the database checksum
        self.update_checksum()

    def write(self):
        """
        Write database to disk
        """
        trace('db.write', self.file_name)
        # Make sure all the changes are saved to the database
        self.sql.update_counters()

        # Export the database to json and encrypt it if a password was defined
        json_data = self.sql_to_json()
        data = json_data if self.crypt_key is None else self.crypt_key.encrypt_str2byte(json_data)

        # Write the data to a temporary file first
        with open(TEMP_FILE, self.write_mode()) as f:
            f.write(data)
        f.close()

        # Rename files. The old file is renamed using a time stamp.
        if os.path.exists(self.file_name):
            os.rename(self.file_name, self.file_name + '-' + get_string_timestamp())
        os.rename(TEMP_FILE, self.file_name)

        # Update the database checksum
        self.update_checksum()

    def close(self):
        """
        Close the database
        """
        self.sql.connection.close()

    def dump(self):
        """
        Dump database contents to the terminal (debugging)
        """
        print_line()
        tag_mapping = self.sql.get_tag_table_name_mapping()
        field_mapping = self.sql.get_field_table_name_mapping()
        print('Tags')
        for t_id, t_name, t_count in self.sql.get_tag_table_list():
            print(f'\t{t_id:2} {t_name} {t_count}')
        print('Fields')
        for f_id, f_name, f_sensitive, f_count in self.sql.get_field_table_list():
            print(f'\t{f_id:2} {f_name} {bool(f_sensitive)} {f_count}')
        print('Items')
        item_dict = self._items_to_dict()
        for i_id in item_dict:
            print(f'\t{i_id}')
            item = item_dict[i_id]
            tag_list = [(tag_mapping[_][MAP_TAG_ID], _) for _ in item[KEY_TAGS]]
            field_dict = item[KEY_FIELDS]
            print(f'\t\tname={item[KEY_NAME]}')
            print(f'\t\tdate={item[KEY_TIMESTAMP]} ({timestamp_to_string(item[KEY_TIMESTAMP])})')
            print(f'\t\tnote={filter_control_characters(item[KEY_NOTE])}')
            print(f'\t\ttags={tag_list}')
            for f_id in field_dict:
                field = field_dict[f_id]
                f_tid = field_mapping[field[KEY_NAME]][MAP_TAG_ID]
                print(f'\t\t{f_id} ({f_tid}) {field[KEY_NAME]} {field[KEY_VALUE]} {field[KEY_ENCRYPTED]}')
        print_line()

    def database_report(self):
        """
        Print a database report (debugging)
        """
        print('File name')
        print(f'\t{self.file_name}')
        print('Key')
        print(f'\t{self.crypt_key}')
        print('Checksums')
        print(f'\tStored  {self.checksum}')
        print(f'\tCurrent {self.calculate_checksum()}')
        print('Table lengths')
        for table in TABLE_LIST:
            n_rows = self.sql.get_table_count(table)
            print(f'\t{table} {n_rows}')
        print('Table schemas')
        for table in TABLE_LIST:
            print(f'\t{table}')
            for _, c_name, c_type, _, _, _ in self.sql.get_table_info(table):
                print(f'\t\t{c_name} {c_type}')


if __name__ == '__main__':
    pass
