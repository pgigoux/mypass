import pytest
from sqlite3 import IntegrityError
from sql import Sql
from sql import INDEX_ID
from sql import INDEX_TAG_TABLE_NAME, INDEX_TAG_TABLE_COUNT
from sql import INDEX_FIELD_TABLE_NAME, INDEX_FIELD_TABLE_SENSITIVE, INDEX_FIELD_TABLE_COUNT
from sql import INDEX_ITEMS_NAME, INDEX_ITEMS_DATE, INDEX_ITEMS_NOTE
from sql import MAP_TAG_ID, MAP_TAG_NAME, MAP_TAG_COUNT
from sql import MAP_FIELD_ID, MAP_FIELD_NAME, MAP_FIELD_SENSITIVE, MAP_FIELD_COUNT


def create_tag_table(sql: Sql):
    """
    Create three arbitrary entries in the tag table
    :param sql: sql object
    """
    sql.insert_into_tag_table(1, 't_one')
    sql.insert_into_tag_table(2, 't_two')
    sql.insert_into_tag_table(3, 't_three')


def create_field_table(sql: Sql):
    """
    Create four arbitrary entries in the field table
    :param sql: sql object
    """
    sql.insert_into_field_table(1, 'f_one', False)
    sql.insert_into_field_table(2, 'f_two', True)
    sql.insert_into_field_table(3, 'f_three', False)
    sql.insert_into_field_table(4, 'f_four', True)


def create_items(sql: Sql):
    """
    Create five arbitrary entries in the items table
    :param sql: sql object
    """
    sql.insert_into_items(1, 'i_one', 1000, 'note 1')
    sql.insert_into_items(2, 'i_two', 2000, 'note 2')
    sql.insert_into_items(3, 'i_three', 3000, 'note 3')
    sql.insert_into_items(4, 'i_four', 4000, 'note 4')
    sql.insert_into_items(5, 'i_five', 5000, 'note 5')


def test_tag_table():
    sql = Sql()

    # Insert (id, name, count)
    assert sql.insert_into_tag_table(None, 't_one') == 1
    assert sql.insert_into_tag_table(None, 't_two') == 2
    assert sql.insert_into_tag_table(4, 't_four') == 4
    assert sql.insert_into_tag_table(3, 't_three', 10) == 3
    assert sql.insert_into_tag_table(None, 't_five') == 5
    with pytest.raises(IntegrityError):
        sql.insert_into_tag_table(3, 't_bad')

    # List
    tag_list = sql.get_tag_table_list()
    assert isinstance(tag_list, list)
    assert len(tag_list) == 5
    assert tag_list == [(1, 't_one', 0), (2, 't_two', 0), (3, 't_three', 10), (4, 't_four', 0), (5, 't_five', 0)]

    # Indices
    assert tag_list[0][INDEX_ID] == 1
    assert tag_list[0][INDEX_TAG_TABLE_NAME] == 't_one'
    assert tag_list[0][INDEX_TAG_TABLE_COUNT] == 0
    assert tag_list[1][INDEX_ID] == 2
    assert tag_list[1][INDEX_TAG_TABLE_NAME] == 't_two'
    assert tag_list[1][INDEX_TAG_TABLE_COUNT] == 0
    assert tag_list[2][INDEX_ID] == 3
    assert tag_list[2][INDEX_TAG_TABLE_NAME] == 't_three'
    assert tag_list[2][INDEX_TAG_TABLE_COUNT] == 10
    assert tag_list[3][INDEX_ID] == 4
    assert tag_list[3][INDEX_TAG_TABLE_NAME] == 't_four'
    assert tag_list[3][INDEX_TAG_TABLE_COUNT] == 0
    assert tag_list[4][INDEX_ID] == 5
    assert tag_list[4][INDEX_TAG_TABLE_NAME] == 't_five'
    assert tag_list[4][INDEX_TAG_TABLE_COUNT] == 0

    # Tag id mapping
    tag_mapping = sql.get_tag_table_id_mapping()
    assert isinstance(tag_mapping, dict)
    assert tag_mapping == {1: ('t_one', 0),
                           2: ('t_two', 0),
                           3: ('t_three', 10),
                           4: ('t_four', 0),
                           5: ('t_five', 0)}

    assert tag_mapping[1][MAP_TAG_NAME] == 't_one'
    assert tag_mapping[1][MAP_TAG_COUNT] == 0

    assert tag_mapping[2][MAP_TAG_NAME] == 't_two'
    assert tag_mapping[2][MAP_TAG_COUNT] == 0

    assert tag_mapping[3][MAP_TAG_NAME] == 't_three'
    assert tag_mapping[3][MAP_TAG_COUNT] == 10

    assert tag_mapping[4][MAP_TAG_NAME] == 't_four'
    assert tag_mapping[4][MAP_TAG_COUNT] == 0

    assert tag_mapping[5][MAP_TAG_NAME] == 't_five'
    assert tag_mapping[5][MAP_TAG_COUNT] == 0

    # Tag name mapping
    tag_mapping = sql.get_tag_table_name_mapping()
    assert isinstance(tag_mapping, dict)
    assert tag_mapping == {'t_one': (1, 0),
                           't_two': (2, 0),
                           't_three': (3, 10),
                           't_four': (4, 0),
                           't_five': (5, 0)}

    assert tag_mapping['t_one'][MAP_TAG_ID] == 1
    assert tag_mapping['t_one'][MAP_TAG_COUNT] == 0

    assert tag_mapping['t_two'][MAP_TAG_ID] == 2
    assert tag_mapping['t_two'][MAP_TAG_COUNT] == 0

    assert tag_mapping['t_three'][MAP_TAG_ID] == 3
    assert tag_mapping['t_three'][MAP_TAG_COUNT] == 10

    assert tag_mapping['t_four'][MAP_TAG_ID] == 4
    assert tag_mapping['t_four'][MAP_TAG_COUNT] == 0

    assert tag_mapping['t_five'][MAP_TAG_ID] == 5
    assert tag_mapping['t_five'][MAP_TAG_COUNT] == 0


def test_field_table():
    sql = Sql()

    # Insert (id, name, sensitive, count)
    assert sql.insert_into_field_table(None, 'f_one', False) == 1
    assert sql.insert_into_field_table(None, 'f_two', True) == 2
    assert sql.insert_into_field_table(None, 'f_three', False, 10) == 3
    assert sql.insert_into_field_table(5, 'f_four', True) == 5
    with pytest.raises(IntegrityError):
        sql.insert_into_field_table(2, 'f_bad', True)

    # List
    field_list = sql.get_field_table_list()
    assert isinstance(field_list, list)
    assert len(field_list) == 4
    assert field_list == [(1, 'f_one', 0, 0), (2, 'f_two', 1, 0), (3, 'f_three', 0, 10), (5, 'f_four', 1, 0)]

    # Indices
    assert field_list[0][INDEX_ID] == 1
    assert field_list[0][INDEX_FIELD_TABLE_NAME] == 'f_one'
    assert bool(field_list[0][INDEX_FIELD_TABLE_SENSITIVE]) is False
    assert field_list[0][INDEX_FIELD_TABLE_COUNT] == 0

    assert field_list[1][INDEX_ID] == 2
    assert field_list[1][INDEX_FIELD_TABLE_NAME] == 'f_two'
    assert bool(field_list[1][INDEX_FIELD_TABLE_SENSITIVE]) is True
    assert field_list[1][INDEX_FIELD_TABLE_COUNT] == 0

    assert field_list[2][INDEX_ID] == 3
    assert field_list[2][INDEX_FIELD_TABLE_NAME] == 'f_three'
    assert bool(field_list[2][INDEX_FIELD_TABLE_SENSITIVE]) is False
    assert field_list[2][INDEX_FIELD_TABLE_COUNT] == 10

    assert field_list[3][INDEX_ID] == 5
    assert field_list[3][INDEX_FIELD_TABLE_NAME] == 'f_four'
    assert bool(field_list[3][INDEX_FIELD_TABLE_SENSITIVE]) is True
    assert field_list[3][INDEX_FIELD_TABLE_COUNT] == 0

    # Field id mapping
    field_mapping = sql.get_field_table_id_mapping()
    assert isinstance(field_mapping, dict)
    assert field_mapping == {1: ('f_one', False, 0), 2: ('f_two', True, 0), 3: ('f_three', False, 10),
                             5: ('f_four', True, 0)}

    assert field_mapping[1][MAP_FIELD_NAME] == 'f_one'
    assert bool(field_mapping[1][MAP_FIELD_SENSITIVE]) is False
    assert field_mapping[1][MAP_FIELD_COUNT] == 0

    assert field_mapping[2][MAP_FIELD_NAME] == 'f_two'
    assert bool(field_mapping[2][MAP_FIELD_SENSITIVE]) is True
    assert field_mapping[2][MAP_FIELD_COUNT] == 0

    assert field_mapping[3][MAP_FIELD_NAME] == 'f_three'
    assert bool(field_mapping[3][MAP_FIELD_SENSITIVE]) is False
    assert field_mapping[3][MAP_FIELD_COUNT] == 10

    assert field_mapping[5][MAP_FIELD_NAME] == 'f_four'
    assert bool(field_mapping[5][MAP_FIELD_SENSITIVE]) is True
    assert field_mapping[5][MAP_FIELD_COUNT] == 0

    # Field name mapping
    field_mapping = sql.get_field_table_name_mapping()
    assert isinstance(field_mapping, dict)
    assert field_mapping == {'f_one': (1, False, 0), 'f_two': (2, True, 0), 'f_three': (3, False, 10),
                             'f_four': (5, True, 0)}

    assert field_mapping['f_one'][MAP_FIELD_ID] == 1
    assert field_mapping['f_one'][MAP_FIELD_SENSITIVE] is False
    assert field_mapping['f_one'][MAP_FIELD_COUNT] == 0

    assert field_mapping['f_two'][MAP_FIELD_ID] == 2
    assert field_mapping['f_two'][MAP_FIELD_SENSITIVE] is True
    assert field_mapping['f_two'][MAP_FIELD_COUNT] == 0

    assert field_mapping['f_three'][MAP_FIELD_ID] == 3
    assert field_mapping['f_three'][MAP_FIELD_SENSITIVE] is False
    assert field_mapping['f_three'][MAP_FIELD_COUNT] == 10

    assert field_mapping['f_four'][MAP_FIELD_ID] == 5
    assert field_mapping['f_four'][MAP_FIELD_SENSITIVE] is True
    assert field_mapping['f_four'][MAP_FIELD_COUNT] == 0


def test_items():
    sql = Sql()

    # Create tag and field tables
    create_tag_table(sql)
    create_field_table(sql)
    assert len(sql.get_tag_table_list()) == 3
    assert len(sql.get_field_table_list()) == 4

    # Insert
    assert sql.insert_into_items(None, 'i_one', 1000, 'note 1') == 1
    assert sql.insert_into_items(None, 'i_two', 2000, 'note 2') == 2
    assert sql.insert_into_items(None, 'i_three', 3000, 'note 3') == 3
    assert sql.insert_into_items(None, 'i_four', 4000, 'note 4') == 4
    assert sql.insert_into_items(200, 'i_five', 5000, 'note 5') == 200

    # List
    item_list = sql.get_item_list()
    assert isinstance(item_list, list)
    assert len(item_list) == 5
    assert item_list == [(1, 'i_one', 1000, 'note 1'),
                         (2, 'i_two', 2000, 'note 2'),
                         (3, 'i_three', 3000, 'note 3'),
                         (4, 'i_four', 4000, 'note 4'),
                         (200, 'i_five', 5000, 'note 5')]
    assert sql.get_item_list(item_id=1) == [(1, 'i_one', 1000, 'note 1')]
    assert sql.get_item_list(item_id=2) == [(2, 'i_two', 2000, 'note 2')]
    assert sql.get_item_list(item_id=3) == [(3, 'i_three', 3000, 'note 3')]
    assert sql.get_item_list(item_id=4) == [(4, 'i_four', 4000, 'note 4')]
    assert sql.get_item_list(item_id=200) == [(200, 'i_five', 5000, 'note 5')]
    assert len(sql.get_item_list(item_id=300)) == 0

    # Indices
    assert item_list[0][INDEX_ID] == 1
    assert item_list[0][INDEX_ITEMS_NAME] == 'i_one'
    assert item_list[0][INDEX_ITEMS_DATE] == 1000
    assert item_list[0][INDEX_ITEMS_NOTE] == 'note 1'

    assert item_list[1][INDEX_ID] == 2
    assert item_list[1][INDEX_ITEMS_NAME] == 'i_two'
    assert item_list[1][INDEX_ITEMS_DATE] == 2000
    assert item_list[1][INDEX_ITEMS_NOTE] == 'note 2'

    assert item_list[2][INDEX_ID] == 3
    assert item_list[2][INDEX_ITEMS_NAME] == 'i_three'
    assert item_list[2][INDEX_ITEMS_DATE] == 3000
    assert item_list[2][INDEX_ITEMS_NOTE] == 'note 3'

    assert item_list[3][INDEX_ID] == 4
    assert item_list[3][INDEX_ITEMS_NAME] == 'i_four'
    assert item_list[3][INDEX_ITEMS_DATE] == 4000
    assert item_list[3][INDEX_ITEMS_NOTE] == 'note 4'

    assert item_list[4][INDEX_ID] == 200
    assert item_list[4][INDEX_ITEMS_NAME] == 'i_five'
    assert item_list[4][INDEX_ITEMS_DATE] == 5000
    assert item_list[4][INDEX_ITEMS_NOTE] == 'note 5'

    # Delete
    assert sql.delete_from_items(2) == 1
    item_list = sql.get_item_list()
    assert len(item_list) == 4
    assert item_list == [(1, 'i_one', 1000, 'note 1'),
                         (3, 'i_three', 3000, 'note 3'),
                         (4, 'i_four', 4000, 'note 4'),
                         (200, 'i_five', 5000, 'note 5')]

    # Update
    assert sql.update_item(1, '', 6000, '') == 1
    assert sql.get_item_list(item_id=1) == [(1, 'i_one', 6000, 'note 1')]

    assert sql.update_item(1, 'new_one', 7000, '') == 1
    assert sql.get_item_list(item_id=1) == [(1, 'new_one', 7000, 'note 1')]

    assert sql.update_item(1, '', 8000, 'new note 1') == 1
    assert sql.get_item_list(item_id=1) == [(1, 'new_one', 8000, 'new note 1')]

    assert sql.update_item(2, 'two', 8000, 'two two') == 0

    assert sql.update_item(3, 'new_three', 9000, 'new note 3') == 1
    assert sql.get_item_list(item_id=3) == [(3, 'new_three', 9000, 'new note 3')]


def test_tags():
    sql = Sql()

    # Create tag & field tables and items
    create_tag_table(sql)
    create_field_table(sql)
    create_items(sql)
    assert len(sql.get_tag_table_list()) == 3
    assert len(sql.get_field_table_list()) == 4
    assert len(sql.get_item_list()) == 5

    # Insert (tag id, item id)
    assert sql.insert_into_tags(None, 1, 1) == 1
    assert sql.insert_into_tags(None, 1, 2) == 2
    assert sql.insert_into_tags(None, 1, 3) == 3
    assert sql.insert_into_tags(None, 1, 4) == 4

    assert sql.insert_into_tags(None, 2, 2) == 5
    assert sql.insert_into_tags(None, 2, 4) == 6

    assert sql.insert_into_tags(None, 3, 1) == 7
    assert sql.insert_into_tags(None, 3, 5) == 8

    # Exists (tag_id, item_id)
    assert sql.tag_exists(1, 1) is True
    assert sql.tag_exists(1, 2) is True
    assert sql.tag_exists(1, 3) is True
    assert sql.tag_exists(1, 4) is True
    assert sql.tag_exists(1, 5) is False

    assert sql.tag_exists(2, 1) is False
    assert sql.tag_exists(2, 2) is True
    assert sql.tag_exists(2, 3) is False
    assert sql.tag_exists(2, 4) is True
    assert sql.tag_exists(2, 5) is False

    assert sql.tag_exists(3, 1) is True
    assert sql.tag_exists(3, 2) is False
    assert sql.tag_exists(3, 3) is False
    assert sql.tag_exists(3, 4) is False
    assert sql.tag_exists(3, 5) is True

    # Get (item_id)
    tag_list = sql.get_tag_list()  # all items
    assert isinstance(tag_list, list)
    assert len(tag_list) == 8
    assert tag_list == [(1, 1, 1), (2, 1, 2), (3, 1, 3), (4, 1, 4), (5, 2, 2), (6, 2, 4), (7, 3, 1), (8, 3, 5)]

    tag_list = sql.get_tag_list(1)  # item 1
    assert isinstance(tag_list, list)
    assert len(tag_list) == 2
    assert tag_list == [(1, 1, 1), (7, 3, 1)]

    tag_list = sql.get_tag_list(2)  # item 2
    assert isinstance(tag_list, list)
    assert len(tag_list) == 2
    assert tag_list == [(2, 1, 2), (5, 2, 2)]

    tag_list = sql.get_tag_list(3)  # item 2
    assert isinstance(tag_list, list)
    assert len(tag_list) == 1
    assert tag_list == [(3, 1, 3)]

    tag_list = sql.get_tag_list(3)  # item 3
    assert isinstance(tag_list, list)
    assert len(tag_list) == 1
    assert tag_list == [(3, 1, 3)]

    tag_list = sql.get_tag_list(4)  # item 4
    assert isinstance(tag_list, list)
    assert len(tag_list) == 2
    assert tag_list == [(4, 1, 4), (6, 2, 4)]

    tag_list = sql.get_tag_list(5)  # item 5
    assert isinstance(tag_list, list)
    assert len(tag_list) == 1
    assert tag_list == [(8, 3, 5)]

    # Delete non existent tags
    assert (sql.delete_from_tags(2, 1)) == 0
    assert (sql.delete_from_tags(4, 1)) == 0
    assert (sql.delete_from_tags(4, 1)) == 0

    assert (sql.delete_from_tags(3, 2)) == 0
    assert (sql.delete_from_tags(4, 2)) == 0
    assert (sql.delete_from_tags(5, 2)) == 0

    assert (sql.delete_from_tags(2, 3)) == 0
    assert (sql.delete_from_tags(3, 3)) == 0
    assert (sql.delete_from_tags(4, 3)) == 0
    assert (sql.delete_from_tags(5, 3)) == 0

    assert (sql.delete_from_tags(3, 4)) == 0
    assert (sql.delete_from_tags(4, 4)) == 0
    assert (sql.delete_from_tags(5, 4)) == 0

    assert (sql.delete_from_tags(1, 5)) == 0
    assert (sql.delete_from_tags(2, 5)) == 0
    assert (sql.delete_from_tags(4, 5)) == 0
    assert (sql.delete_from_tags(5, 5)) == 0

    # Delete all tags of an item
    assert (sql.delete_from_tags(None, 1)) == 2
    assert sql.tag_exists(1, 1) is False
    assert sql.tag_exists(2, 1) is False
    assert sql.tag_exists(3, 1) is False
    assert sql.tag_exists(4, 1) is False
    assert sql.tag_exists(5, 1) is False
    tag_list = sql.get_tag_list()
    assert len(tag_list) == 6
    assert tag_list == [(2, 1, 2), (3, 1, 3), (4, 1, 4), (5, 2, 2), (6, 2, 4), (8, 3, 5)]

    # Delete single tag of an item
    assert (sql.delete_from_tags(2, 2)) == 1
    assert sql.tag_exists(1, 2) is True
    assert sql.tag_exists(2, 2) is False
    assert sql.tag_exists(3, 2) is False
    assert sql.tag_exists(4, 2) is False
    assert sql.tag_exists(5, 2) is False
    tag_list = sql.get_tag_list()
    assert len(tag_list) == 5
    assert tag_list == [(2, 1, 2), (3, 1, 3), (4, 1, 4), (6, 2, 4), (8, 3, 5)]


def test_fields():
    sql = Sql()

    # Create tag & field tables and items
    create_tag_table(sql)
    create_field_table(sql)
    create_items(sql)
    assert len(sql.get_tag_table_list()) == 3
    assert len(sql.get_field_table_list()) == 4
    assert len(sql.get_item_list()) == 5

    # Insert (field id, item id, value, encrypted)
    # TODO - complete
    assert sql.insert_into_fields(None, 1, 1, 'v_one', False) == 1
    assert sql.insert_into_fields(None, 1, 2, 'v_two', False) == 2
    assert sql.insert_into_fields(None, 1, 3, 'v_three', True) == 3
    assert sql.insert_into_fields(None, 1, 4, 'v_four', True) == 4

    assert sql.insert_into_fields(None, 2, 2, 'v_four', True) == 5
    assert sql.insert_into_fields(None, 2, 4, 'v_four', False) == 6

    assert sql.insert_into_fields(None, 3, 1, 'v_four', True) == 7
    assert sql.insert_into_fields(None, 3, 5, 'v_four', False) == 8


if __name__ == '__main__':
    test_tag_table()
    test_field_table()
    test_items()
    test_tags()
    test_fields()
