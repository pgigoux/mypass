import sqlite3 as sq
from typing import Optional

# List of tables in the database
NAME_TAG_TABLE = 'tag_table'
NAME_FIELD_TABLE = 'field_table'
NAME_TAGS = 'tags'
NAME_FIELDS = 'fields'
NAME_ITEMS = 'items'
TABLE_LIST = [NAME_TAG_TABLE, NAME_FIELD_TABLE, NAME_TAGS, NAME_FIELDS, NAME_ITEMS]

# Indices used to access the elements in the tuples returned by the sql functions
# all tables have the id (primary key) as the first element
INDEX_ID = 0
# tag table
INDEX_TAG_TABLE_NAME = 1
INDEX_TAG_TABLE_COUNT = 2
# field table
INDEX_FIELD_TABLE_NAME = 1
INDEX_FIELD_TABLE_SENSITIVE = 2
INDEX_FIELD_TABLE_COUNT = 3
# tags
INDEX_TAGS_TAG_ID = 1
INDEX_TAGS_ITEM_ID = 2
# fields
INDEX_FIELDS_FIELD_ID = 1
INDEX_FIELDS_ITEM_ID = 2
INDEX_FIELDS_ITEM_VALUE = 3
INDEX_FIELDS_ITEM_ENCRYPTED = 4
# items
INDEX_ITEMS_NAME = 1
INDEX_ITEMS_DATE = 2
INDEX_ITEMS_NOTE = 3

# Indices used to access the elements in the tuples returned by the mapping functions
# tag mapping
MAP_TAG_ID = 0
MAP_TAG_NAME = 0
MAP_TAG_COUNT = 1
# field mapping
MAP_FIELD_ID = 0
MAP_FIELD_NAME = 0
MAP_FIELD_SENSITIVE = 1
MAP_FIELD_COUNT = 2


class Sql:

    def __init__(self):
        """
        Create an sqlite database in memory
        """
        self.connection = sq.connect(':memory:')
        self.cursor = self.connection.cursor()
        self.cursor.execute('pragma foreign_keys = on;')
        self._create_tables()

    def _create_tables(self):
        """
        Create the database tables. The uses four tables to store the data: tag_table,
        field_table, tags, fields and items.
        """
        # Tag table
        table = """
                create table tag_table (
                    id integer primary key autoincrement,
                    name varchar(30) not null,
                    count integer default 0
                );
                """
        self.cursor.execute(table)

        # Field table
        table = """
                create table field_table (
                    id integer primary key autoincrement,
                    name varchar(30) not null,
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
        Print the table structures (debugging)
        :return:
        """
        self._print_table_structure('tag_table')
        self._print_table_structure('field_table')
        self._print_table_structure('items')
        self._print_table_structure('tags')
        self._print_table_structure('fields')

    def _print_table_structure(self, table_name: str):
        """
        Print the structure of a table (debugging)
        :param table_name:
        :return:
        """
        print(f'-- {table_name}')
        tbl = self.cursor.execute(f'pragma table_info({table_name});')
        for _ in tbl:
            print('+', _)

    def dump(self):
        """
        Dump table contents (debugging)
        """
        print('tag_table', self.get_tag_table_list())
        print('field_table', self.get_field_table_list())
        print('tags', self.get_tag_list())
        print('fields', self.get_field_list())
        print('items', self.get_item_list())

    # -------------------------------------------------------------
    # Tag table
    # -------------------------------------------------------------

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
        tmp_list = self.get_tag_table_list()
        return {t_name: (t_id, t_count) for t_id, t_name, t_count in tmp_list}

    def get_tag_table_id_mapping(self) -> dict:
        """
        Return the tag_table as a dictionary indexed by the tag name. Each element of
        the dictionary will contain the tag id and count.
        :return: tag table dictionary
        """
        tmp_list = self.get_tag_table_list()
        return {t_id: (t_name, t_count) for t_id, t_name, t_count in tmp_list}

    def insert_into_tag_table(self, tag_id: int | None, tag_name: str, tag_count: Optional[int] = 0) -> int:
        """
        Insert a new tag into the tag table
        :param tag_id: tag id (or None if autoincrement)
        :param tag_name: tag name
        :param tag_count: number of times the tag is used
        :return tag id
        """
        self.cursor.execute('insert into tag_table values(?,?,?)', (tag_id, tag_name, tag_count))
        return self.cursor.lastrowid if tag_id is None else tag_id

    def delete_from_tag_table(self, tag_name: str):
        """
        Delete a tag from the tag table
        :param tag_name: tag name
        :return: number of changes made (1 if ok, 0 if the tag didn't exist)
        """
        self.cursor.execute('delete from tag_table where name=?', (tag_name,))
        return self.cursor.rowcount

    def rename_tag_table_entry(self, old_name: str, new_name: str) -> int:
        """
        Rename a tag.
        :param old_name: old tag name
        :param new_name: new tag name
        :return: number of changes made (1 if ok, 0 if the tag didn't exist)
        """
        self.cursor.execute(f'update tag_table set name=? where name=?', (new_name, old_name))
        return self.cursor.rowcount

    def search_tag_table(self, pattern: str) -> list:
        """
        Search for a tag that matches a given pattern
        :param pattern: pattern to search for
        :return: list of tags matching the
        """
        self.cursor.execute(f'select * from tag_table where name like ?', (f'%{pattern}%',))
        return self.cursor.fetchall()

    def update_tag_table_counters(self):
        """
        Update the tag table counters
        :return:
        """
        tag_counters = {t: 0 for t, _, _ in self.get_tag_table_list()}
        for item_id, _, _, _ in self.get_item_list():
            for _, t_id, _ in self.get_tag_list(item_id=item_id):
                tag_counters[t_id] += 1
        for t_id, _, _ in self.get_tag_table_list():
            self.cursor.execute('update tag_table set count = ? where id = ?', (tag_counters[t_id], t_id))
        self.connection.commit()

    # -------------------------------------------------------------
    # Field table
    # -------------------------------------------------------------

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
        the dictionary will contain the field name, count and sensitive flag.
        :return:
        """
        tmp_list = self.get_field_table_list()
        return {f_id: (f_name, bool(f_sensitive), f_count) for f_id, f_name, f_sensitive, f_count in tmp_list}

    def get_field_table_name_mapping(self) -> dict:
        """
        Return the field_table as a dictionary indexed by the field name. Each element of
        the dictionary will contain the field id, sensitive flag and count.
        :return:
        """
        tmp_list = self.get_field_table_list()
        return {f_name: (f_id, bool(f_sensitive), f_count) for f_id, f_name, f_sensitive, f_count in tmp_list}

    def insert_into_field_table(self, field_id: int | None, field_name: str, field_sensitive: bool,
                                field_count: Optional[int] = 0) -> int:
        """
        Insert a new field into the field table
        :param field_id: field id (or None if autoincrement)
        :param field_name: field name
        :param field_sensitive: sensitive data?
        :param field_count: number of times the field is used
        :return field id
        """
        self.cursor.execute('insert into field_table values(?,?,?,?)',
                            (field_id, field_name, field_sensitive, field_count))
        return self.cursor.lastrowid if field_id is None else field_id

    def delete_from_field_table(self, field_name: str):
        """
        Delete a tag from the tag table
        :param field_name: field name
        :return: number of changes made (1 if ok, 0 if the field didn't exist)
        """
        self.cursor.execute('delete from field_table where name=?', (field_name,))
        return self.cursor.rowcount

    def rename_field_table_entry(self, old_name: str, new_name: str) -> int:
        """
        Rename a tag.
        :param old_name: old field name
        :param new_name: new field name
        :return: number of changes made (1 if ok, 0 if the tag didn't exist)
        """
        self.cursor.execute(f'update field_table set name=? where name=?', (new_name, old_name))
        return self.cursor.rowcount

    def search_field_table(self, pattern: str) -> list:
        """
        Search for a field that matches a given pattern
        :param pattern: pattern to search for
        :return: list of fields matching the
        """
        self.cursor.execute(f'select * from field_table where name like ?', (f'%{pattern}%',))
        return self.cursor.fetchall()

    def update_field_table_counters(self):
        """
        Update the field table counters
        """
        field_counters = {f: 0 for f, _, _, _ in self.get_field_table_list()}
        for item_id, _, _, _ in self.get_item_list():
            for _, f_id, _, _, f_count in self.get_field_list(item_id=item_id):
                field_counters[f_id] += 1
        for f_id, _, _, _ in self.get_field_table_list():
            self.cursor.execute('update field_table set count = ? where id = ?', (field_counters[f_id], f_id))
        self.connection.commit()

    # -------------------------------------------------------------
    # Tags
    # -------------------------------------------------------------

    def tag_exists(self, tag_id: int, item_id: int) -> bool:
        """
        Check whether an item has a tag
        :param tag_id: tag id from tag table
        :param item_id: item id
        :return: True it it exists, False otherwise
        """
        self.cursor.execute(f'select * from tags where item_id=? and tag_id=?', (item_id, tag_id))
        return len(self.cursor.fetchall()) > 0

    def get_tag_list(self, item_id: Optional[int] = None) -> list:
        """
        Select all tags for a given item id, or all tags if item id is None.
        Return a list of tuples containing the tag id, tag table id and item id.
        :param item_id: item id
        :return: list of tuples with tag data
        """
        cmd = f'select * from tags' if item_id is None else f'select * from tags where item_id={item_id}'
        self.cursor.execute(cmd)
        return self.cursor.fetchall()

    def insert_into_tags(self, tag_id: int | None, tag_table_id: int, item_id: int) -> int:
        """
        Insert a new tag
        :param tag_id: tag id (or None if autoincrement)
        :param tag_table_id: tag id from the tag_table
        :param item_id: item id the tag is associated with
        :return tag id
        """
        self.cursor.execute('insert into tags values(?,?,?)', (tag_id, tag_table_id, item_id))
        return self.cursor.lastrowid if tag_id is None else tag_id

    def delete_from_tags(self, tag_table_id: int | None, item_id: int) -> int:
        """
        Remove tags associated with a given item id
        :param tag_table_id: tag id from tag table
        :param item_id: item id
        :return: number of rows deleted
        """
        cmd = f'delete from tags where item_id={item_id}' if tag_table_id is None \
            else f'delete from tags where tag_id={tag_table_id} and item_id={item_id}'
        self.cursor.execute(cmd)
        return self.cursor.rowcount

    # -------------------------------------------------------------
    # Fields
    # -------------------------------------------------------------

    def field_exists(self, field_id: int, item_id: int) -> bool:
        """
        Check whether an item has a tag
        :param field_id: field id from field table
        :param item_id: item id
        :return: True it it exists, False otherwise
        """
        self.cursor.execute(f'select * from fields where item_id=? and field_id=?', (item_id, field_id))
        return len(self.cursor.fetchall()) > 0

    def get_field_list(self, item_id: Optional[int] = None) -> list:
        """
        Select all fields for a given item id, or all fields if item id is None.
        Return a list of tuples containing the field id, field table id, item id, field value and encrypted value flag
        :param item_id: item id
        :return: list of tuples with field data
        """
        cmd = f'select * from fields' if item_id is None else f'select * from fields where item_id={item_id}'
        self.cursor.execute(cmd)
        return self.cursor.fetchall()

    def insert_into_fields(self, field_id: int | None, field_table_id: int, item_id: int,
                           field_value: str, encrypted_value=False) -> int:
        """
        Insert a new field
        :param field_id: field id (or None if autoincrement)
        :param field_table_id: field id from the field_table
        :param item_id: item id the field belongs to
        :param field_value: field value
        :param encrypted_value: is value encrypted?
        :return field id
        """
        self.cursor.execute('insert into fields values (?,?,?,?,?)',
                            (field_id, field_table_id, item_id, field_value, encrypted_value))
        return self.cursor.lastrowid if field_id is None else field_id

    def delete_from_fields(self, field_table_id: int | None, item_id: int) -> int:
        """
        Remove fields associated with a given item id
        :param field_table_id: field id from field table
        :param item_id: item id
        :return: number of rows deleted
        """
        # self.cursor.execute('delete from fields where item_id=?', (item_id,))
        cmd = f'delete from fields where item_id={item_id}' if field_table_id is None \
            else f'delete from fields where field_id={field_table_id} and item_id={item_id}'
        self.cursor.execute(cmd)
        return self.cursor.rowcount

    def update_field(self, field_id: int, item_id: int, field_table_id: Optional[int] = None,
                     field_value: Optional[str] = None, encrypted_value: Optional[bool] = None) -> int:
        """
        Update field value, encrypted flag and field table id.
        The item id is redundant, but it's used to double check the correct field is being updated.
        :param field_id: field id
        :param item_id: item id
        :param field_table_id: field id from field table
        :param field_value: field value
        :param encrypted_value: is value encrypted?
        :return number of rows updated (1 if successful, 0 otherwise)
        """
        if field_table_id is None and field_value is None and encrypted_value is None:
            return 0
        comma = ''
        cmd = 'update fields set '
        if field_table_id is not None:
            cmd += f'{comma}field_id={field_table_id}'
            comma = ', '
        if field_value is not None:
            cmd += f'{comma}value="{field_value}"'
            comma = ', '
        if encrypted_value is not None:
            cmd += f'{comma}encrypted={encrypted_value}'
        cmd += f' where id={field_id} and item_id={item_id}'
        self.cursor.execute(cmd)
        return self.cursor.rowcount

    # -------------------------------------------------------------
    # Items
    # -------------------------------------------------------------

    def get_item_list(self, item_id: Optional[int] = None) -> list:
        """
        Select all items for a given item id, or all items if item id is None.
        Return a list of tuples containing the item id, item name, timestamp and  note.
        :param item_id: item id
        :return: list of tuples with item data
        """
        cmd = f'select * from items' if item_id is None else f'select * from items where id={item_id}'
        self.cursor.execute(cmd)
        return self.cursor.fetchall()

    def insert_into_items(self, item_id: int | None, item_name: str, item_timestamp: int, item_note: str) -> int:
        """
        Insert a new item
        :param item_id: item id (or None if autoincrement)
        :param item_name: item name
        :param item_timestamp: time stamp
        :param item_note: note
        :return item id
        """
        self.cursor.execute('insert into items values(?,?,?,?)',
                            (item_id, item_name, item_timestamp, item_note))
        return self.cursor.lastrowid if item_id is None else item_id

    def delete_from_items(self, item_id: int) -> int:
        """
        Remove an item associated with a given item id
        :param item_id: item id
        :return: number of rows deleted (1 if successful, 0 otherwise)
        """
        self.cursor.execute('delete from items where id=?', (item_id,))
        return self.cursor.rowcount

    def update_item(self, item_id: int, item_timestamp: int,
                    item_name: Optional[str] = None, item_note: Optional[str] = None) -> int:
        """
        Update an existing item
        :param item_id: item id
        :param item_timestamp: time stamp
        :param item_name: item name
        :param item_note: note
        :return: number of rows updated (1 if successful, 0 otherwise)
        """
        cmd = f'update items set date={item_timestamp}'
        if item_name is not None:
            cmd += f', name="{item_name}"'
        if item_note is not None:
            cmd += f', note="{item_note}"'
        cmd += f' where id={item_id}'
        self.cursor.execute(cmd)
        return self.cursor.rowcount

    # -------------------------------------------------------------
    # General
    # -------------------------------------------------------------

    def update_counters(self):
        """
        Update the tag and field table counters
        :return:
        """
        self.update_tag_table_counters()
        self.update_field_table_counters()

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
        self.connection.commit()
        c = sq.connect(file_name)
        self.connection.backup(c)
        c.close()

    def get_table_count(self, table: str) -> int:
        """
        Get the number of rows in a table
        :param table: table name
        :return: number of rows
        """
        self.cursor.execute(f'select count() from {table}')
        return int(self.cursor.fetchone()[0])

    def get_table_info(self, table: str) -> list:
        """
        Get the table structure
        :param table: table name
        :return: list with table information
        """
        self.cursor.execute(f"pragma table_info('{table}')")
        return self.cursor.fetchall()


if __name__ == '__main__':
    sql = Sql()

    # def update_field(field_id, field_table_id, field_value, encrypted_value) -> int:
    # print(sql.update_field(10, None, "two", True))

    # print('-- insert tag table --')
    # print(sql.insert_into_tag_table(None, 't_one'))
    # print(sql.insert_into_tag_table(None, 't_two'))
    # print(sql.insert_into_tag_table(None, 't_three'))
    #
    # print('-- insert field table --')
    # print(sql.insert_into_field_table(None, 'f_one', False))
    # print(sql.insert_into_field_table(None, 'f_two', True))
    # print(sql.insert_into_field_table(None, 'f_three', False))
    # print(sql.insert_into_field_table(None, 'f_four', True))
    #
    # print('-- insert items --')
    # print(sql.insert_into_items(None, 'i_one', 1000, 'note 1'))
    # print(sql.insert_into_items(None, 'i_two', 2000, 'note 2'))
    # print(sql.insert_into_items(None, 'i_three', 3000, 'note 3'))
    # print(sql.insert_into_items(None, 'i_four', 4000, 'note 4'))
    # print(sql.insert_into_items(None, 'i_five', 5000, 'note 5'))
    #
    # print('-- insert tags --')
    # print(sql.insert_into_tags(None, 1, 1))
    # print(sql.insert_into_tags(None, 1, 2))
    # print(sql.insert_into_tags(None, 2, 3))
    # print(sql.insert_into_tags(None, 1, 4))
    # print(sql.insert_into_tags(None, 2, 1))
    # print(sql.insert_into_tags(None, 2, 5))
    #
    # print('-- insert fields --')
    # print(sql.insert_into_fields(None, 1, 1, 'f_one', False))
    # print(sql.insert_into_fields(None, 2, 1, 'f_two', False))
    # print(sql.insert_into_fields(None, 3, 2, 'f_three', False))
    # print(sql.insert_into_fields(None, 4, 3, 'f_four', False))
    # print(sql.insert_into_fields(None, 1, 4, 'f_five', False))
    # print(sql.insert_into_fields(None, 2, 5, 'f_six', False))
    #
    # print('-- get tags --')
    # print(sql.get_tag_list(item_id=1))
    # print(sql.get_tag_list(item_id=2))
    # print(sql.get_tag_list(item_id=3))
    # print(sql.get_tag_list(item_id=4))
    # print(sql.get_tag_list(item_id=5))
    # print(sql.get_tag_list(item_id=6))
    #
    # print('-- get fields --')
    # print(sql.get_field_list(item_id=1))
    # print(sql.get_field_list(item_id=2))
    # print(sql.get_field_list(item_id=3))
    # print(sql.get_field_list(item_id=4))
    # print(sql.get_field_list(item_id=5))
    # print(sql.get_field_list(item_id=6))
    #
    # print(sql.tag_exists(1, 1))
    # print(sql.tag_exists(2, 1))
    # print(sql.tag_exists(3, 1))
    #
    # print(sql.field_exists(1, 1))
    # print(sql.field_exists(2, 1))
    # print(sql.field_exists(3, 1))
    #
    # # sql.export_to_sql('junk.db')

    # print('-' * 20)
    # sql.dump()
