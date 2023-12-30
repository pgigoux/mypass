import os
import json
import sqlite3 as sq
from crypt import Crypt
from utils import filter_control_characters, timestamp_to_string, get_string_timestamp

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

# Temporary file used when saving database
TEMP_FILE = 'db.tmp'


class Database:

    def __init__(self, file_name: str, password=''):
        """
        :param file_name: database file name
        :param password: password to encode data
        """
        self.file_name = file_name
        self.password = password
        self.connection = sq.connect(':memory:')
        self.cursor = self.connection.cursor()
        self.create_tables()
        # The database will be encrypted if a password is supplied
        self.crypt_key = Crypt(password) if password else None

    def create_tables(self):
        """
        Create the database tables. The uses four tables to store the data: tag_table,
        field_table, tags, fields and items.
        """
        # Tag table
        table = """
                create table tag_table (
                    id integer primary key autoincrement,
                    name varchar(25) not null,
                    count integer default 0
                );
                """
        self.cursor.execute(table)

        # Field table
        table = """
                create table field_table (
                    id integer primary key autoincrement,
                    name varchar(25) not null,
                    sensitive bool default false,
                    count integer default 0
                );
                """
        self.cursor.execute(table)

        # Items
        table = """
                create table items (
                    id integer primary key autoincrement,
                    name varchar(30) not null,
                    date integer not null,
                    note text
                );
                """
        self.cursor.execute(table)

        # Tags
        table = """
                create table tags (
                    id integer primary key autoincrement,
                    tag_id integer not null,
                    item_id integer not null,
                    foreign key(tag_id) references tag_table(id),
                    foreign key(item_id) references items(id)
                );
                """
        self.cursor.execute(table)

        # Fields
        table = """
                create table fields (
                    id integer primary key autoincrement,
                    field_id integer not null,
                    item_id integer not null,
                    value text not null,
                    encrypted bool default false,
                    foreign key(item_id) references items(id)
                    foreign key(field_id) references field_table(id)
                );
                """
        self.cursor.execute(table)
        self.connection.commit()

    def print_tables(self):
        """
        Print the table structures
        :return:
        """
        self._print_table_structure('tag_table')
        self._print_table_structure('field_table')
        self._print_table_structure('items')
        self._print_table_structure('tags')
        self._print_table_structure('fields')

    def _print_table_structure(self, table_name: str):
        """
        Print the structure of a table
        :param table_name:
        :return:
        """
        print(f'-- {table_name}')
        tbl = self.cursor.execute(f'pragma table_info({table_name});')
        for _ in tbl:
            print('+', _)

    def get_tag_table_list(self) -> list:
        """
        Return the tag_table as a list of tuples containing the tag id, tag name
        and tag count.
        :return: tag list
        """
        self.cursor.execute('select * from tag_table')
        return self.cursor.fetchall()

    def get_tag_table_name_mapping(self) -> dict:
        """
        Return the tag_table as a dictionary indexed by the tag id. Each element of
        the dictionary will contain the tag name and count.
        :return: tag table dictionary
        """
        self.cursor.execute('select * from tag_table')
        return {t_name: (t_id, t_count) for t_id, t_name, t_count in self.cursor.fetchall()}

    def get_tag_table_id_mapping(self) -> dict:
        """
        Return the tag_table as a dictionary indexed by the tag name. Each element of
        the dictionary will contain the tag id and count.
        :return: tag table dictionary
        """
        self.cursor.execute('select * from tag_table')
        return {t_id: (t_name, t_count) for t_id, t_name, t_count in self.cursor.fetchall()}

    def get_field_table_list(self) -> list:
        """
        Return the field_table as a list of tuples containing the field id, field name,
        sensitive flag and count.
        and tag count.
        :return: field list
        """
        self.cursor.execute('select * from field_table')
        return self.cursor.fetchall()

    def get_field_table_id_mapping(self) -> dict:
        """
        Return the field_table as a dictionary indexed by the field id. Each element of
        the dictionary will contain the field name, sensitive flag and count.
        :return:
        """
        self.cursor.execute('select * from field_table')
        return {f_id: (f_name, bool(f_sensitive), f_count) for f_id, f_name, f_sensitive, f_count in
                self.cursor.fetchall()}

    def get_field_table_name_mapping(self) -> dict:
        """
        Return the field_table as a dictionary indexed by the field name. Each element of
        the dictionary will contain the field id, sensitive flag and count.
        :return:
        """
        self.cursor.execute('select * from field_table')
        return {f_name: (f_id, bool(f_sensitive), f_count) for f_id, f_name, f_sensitive, f_count in
                self.cursor.fetchall()}

    def tag_table_to_list(self) -> list:
        """
        Return the tag_table as a list of where each element is the tag id, tag name and count.
        :return:
        """
        self.cursor.execute(f'select * from tag_table')
        fetch_list = self.cursor.fetchall()
        # print(tag_list)
        output_list = []
        for tag_id, t_name, t_count in fetch_list:
            output_list.append({KEY_ID: tag_id, KEY_NAME: t_name, KEY_COUNT: t_count})
        return output_list

    def field_table_to_list(self) -> list:
        """
        Return the tag_table as a list of where each element is a dictionary
        containing the tag id, tag name and count.
        :return:
        """
        self.cursor.execute(f'select * from field_table')
        fetch_list = self.cursor.fetchall()
        output_list = []
        for f_id, f_name, f_sensitive, f_count in fetch_list:
            output_list.append({KEY_ID: f_id, KEY_NAME: f_name, KEY_SENSITIVE: bool(f_sensitive), KEY_COUNT: f_count})
        return output_list

    def items_to_dict(self, decrypt_flag=False) -> dict:
        """
        Convert the items in the database into a dictionary. Aside from the fixed
        item attributes (name, timestamp, note), the dictionary also contains the
        list of tags and a dictionary with the field information.
        :param decrypt_flag: decrypt field values if encryption is enabled?
        :return: dictionary with items
        """
        output_dict = {}

        # Get the tag and field mappings to convert ids into names
        tag_mapping = self.get_tag_table_id_mapping()
        field_mapping = self.get_field_table_id_mapping()

        # Query the database to get all items
        self.cursor.execute('select * from items')
        item_fetch_list = self.cursor.fetchall()

        # Iterate over all items
        for item_id, item_name, item_date, item_note in item_fetch_list:
            # Item fixed attributes
            item_dict = {KEY_NAME: item_name, KEY_TIMESTAMP: item_date, KEY_NOTE: item_note}

            # Process the item tags
            self.cursor.execute(f'select * from tags where item_id={item_id}')
            tag_fetch_list = self.cursor.fetchall()
            item_dict[KEY_TAGS] = [tag_mapping[tag_id][0] for _, tag_id, _ in tag_fetch_list]

            # Process the item fields
            self.cursor.execute(f'select * from fields where item_id={item_id}')
            field_fetch_list = self.cursor.fetchall()
            field_dict = {}
            for field_id, f_id, _, field_value, f_encrypted in field_fetch_list:
                if decrypt_flag and f_encrypted and db.crypt_key is not None:
                    field_value = db.crypt_key.decrypt_str2str(field_value)
                tmp_dict = {KEY_NAME: field_mapping[f_id][0], KEY_VALUE: field_value,
                            KEY_ENCRYPTED: bool(f_encrypted)}
                field_dict[field_id] = tmp_dict
            item_dict[KEY_FIELDS] = field_dict

            output_dict[item_id] = item_dict

        return output_dict

    def convert_to_json(self) -> str:
        """
        Convert the database to json
        :return: json string
        """
        d = {KEY_TAG_SECTION: self.tag_table_to_list(),
             KEY_FIELD_SECTION: self.field_table_to_list(),
             KEY_ITEM_SECTION: self.items_to_dict()}
        return json.dumps(d)

    def dump(self):
        """
        Dump database contents to the terminal (debugging)
        """
        tag_mapping = self.get_tag_table_name_mapping()
        field_mapping = self.get_field_table_name_mapping()

        print('Tags')
        for t_id, t_name, t_count in self.get_tag_table_list():
            print(f'\t{t_id:2} {t_name} {t_count}')
        print('Fields')
        for f_id, f_name, f_sensitive, f_count in self.get_field_table_list():
            print(f'\t{f_id:2} {f_name} {bool(f_sensitive)} {f_count}')
        print('Items')
        item_dict = self.items_to_dict()
        for i_id in item_dict:
            print(f'\t{i_id}')
            item = item_dict[i_id]
            tag_list = [(tag_mapping[_][0], _) for _ in item[KEY_TAGS]]
            field_dict = item[KEY_FIELDS]
            print(f'\t\tname={item[KEY_NAME]}')
            print(f'\t\tdate={item[KEY_TIMESTAMP]} ({timestamp_to_string(item[KEY_TIMESTAMP])})')
            print(f'\t\tnote={filter_control_characters(item[KEY_NOTE])}')
            print(f'\t\ttags={tag_list}')
            for f_id in field_dict:
                field = field_dict[f_id]
                f_tid = field_mapping[field[KEY_NAME]][0]
                print(f'\t\t{f_id} ({f_tid}) {field[KEY_NAME]} {field[KEY_VALUE]} {field[KEY_ENCRYPTED]}')

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

    def import_from_json(self):
        """
        TODO - low priority
        """
        pass

    def export_to_json(self, file_name: str):
        """
        :return:
        """
        with open(file_name, 'w') as f:
            f.write(self.convert_to_json())
        f.close()

    def import_from_sql(self, file_name: str):
        """
        Import the database from an sqlite file
        :param file_name: output file name
        :return:
        """
        sc = sq.connect(file_name)
        dc = self.connection
        sc.backup(dc)

    def export_to_sql(self, file_name: str):
        """
        Export the database to an sqlite file
        :param file_name: output file name
        :return:
        """
        c = sq.connect(file_name)
        self.connection.backup(c)
        c.close()

    def read(self):
        with open(self.file_name, self.read_mode()) as f_in:
            data = f_in.read()
            if self.crypt_key is not None:
                assert isinstance(data, bytes)
                try:
                    data = self.crypt_key.decrypt_byte2str(data)
                except Exception as e:
                    raise ValueError(f'failed to decrypt data: {repr(e)}')

        try:
            json_data = json.loads(data)
        except Exception as e:
            raise ValueError(f'failed to read the data: {repr(e)}')

        print(json_data)

    def write(self):
        """
        Write database to disk
        """
        json_data = self.convert_to_json()
        data = json_data if self.crypt_key is None else self.crypt_key.encrypt_str2byte(json_data)

        # Write the data to a temporary file first
        with open(TEMP_FILE, self.write_mode()) as f_out:
            f_out.write(data)
        f_out.close()

        # Rename files. The old file is renamed using a time stamp.
        if os.path.exists(self.file_name):
            os.rename(self.file_name, self.file_name + '-' + get_string_timestamp())
        os.rename(TEMP_FILE, self.file_name)


if __name__ == '__main__':
    db = Database('pw.db', password='test')
    db.read()
    # db.import_from_sql('backup.db')
    # db.dump()
    # db.write()

    # db.cursor.execute('insert into tag_table values (?,?,?)', (None, 't_one', 0))
    # db.cursor.execute('insert into tag_table values (?,?,?)', (None, 't_two', 0))
    # print(db.get_tag_table_id_mapping())
    # print(db.get_tag_table_name_mapping())

    # db.cursor.execute('insert into field_table values (?,?,?,?)', (None, 'f_one', False, 0))
    # db.cursor.execute('insert into field_table values (?,?,?,?)', (None, 'f_two', True, 0))
    # db.cursor.execute('insert into field_table values (?,?,?,?)', (None, 'f_three', False, 0))
    # print(db.get_field_table_id_mapping())
    # print(db.get_field_table_name_mapping())
