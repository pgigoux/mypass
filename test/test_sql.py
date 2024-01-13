import pytest
from sqlite3 import IntegrityError
from sql import Sql
from sql import INDEX_ID
from sql import INDEX_TAG_TABLE_NAME, INDEX_TAG_TABLE_COUNT
from sql import INDEX_FIELD_TABLE_NAME, INDEX_FIELD_TABLE_SENSITIVE, INDEX_FIELD_TABLE_COUNT
from sql import MAP_TAG_ID, MAP_TAG_NAME, MAP_TAG_COUNT
from sql import MAP_FIELD_ID, MAP_FIELD_NAME, MAP_FIELD_SENSITIVE, MAP_FIELD_COUNT

"""
sql = Sql()

    print('-- insert tag table --')
    print(sql.insert_into_tag_table(None, 't_one'))
    print(sql.insert_into_tag_table(None, 't_two'))
    print(sql.insert_into_tag_table(None, 't_three'))

    print('-- insert field table --')
    print(sql.insert_into_field_table(None, 'f_one', False))
    print(sql.insert_into_field_table(None, 'f_two', True))
    print(sql.insert_into_field_table(None, 'f_three', False))
    print(sql.insert_into_field_table(None, 'f_four', True))

    print('-- insert items --')
    print(sql.insert_into_items(None, 'i_one', 1000, 'note 1'))
    print(sql.insert_into_items(None, 'i_two', 2000, 'note 2'))
    print(sql.insert_into_items(None, 'i_three', 3000, 'note 3'))
    print(sql.insert_into_items(None, 'i_four', 4000, 'note 4'))
    print(sql.insert_into_items(None, 'i_five', 5000, 'note 5'))

    print('-- insert tags --')
    print(sql.insert_into_tags(None, 1, 1))
    print(sql.insert_into_tags(None, 1, 2))
    print(sql.insert_into_tags(None, 2, 3))
    print(sql.insert_into_tags(None, 1, 4))
    print(sql.insert_into_tags(None, 2, 1))
    print(sql.insert_into_tags(None, 2, 5))

    print('-- insert fields --')
    print(sql.insert_into_fields(None, 1, 1, 'f_one', False))
    print(sql.insert_into_fields(None, 2, 1, 'f_two', False))
    print(sql.insert_into_fields(None, 3, 2, 'f_three', False))
    print(sql.insert_into_fields(None, 4, 3, 'f_four', False))
    print(sql.insert_into_fields(None, 1, 4, 'f_five', False))
    print(sql.insert_into_fields(None, 2, 5, 'f_six', False))

    print('-- get tags --')
    print(sql.get_tag_list(item_id=1))
    print(sql.get_tag_list(item_id=2))
    print(sql.get_tag_list(item_id=3))
    print(sql.get_tag_list(item_id=4))
    print(sql.get_tag_list(item_id=5))
    print(sql.get_tag_list(item_id=6))

    print('-- get fields --')
    print(sql.get_field_list(item_id=1))
    print(sql.get_field_list(item_id=2))
    print(sql.get_field_list(item_id=3))
    print(sql.get_field_list(item_id=4))
    print(sql.get_field_list(item_id=5))
    print(sql.get_field_list(item_id=6))
"""


def test_tag_table():
    sql = Sql()

    # Insert
    assert sql.insert_into_tag_table(None, 't_one') == 1
    assert sql.insert_into_tag_table(None, 't_two') == 2
    assert sql.insert_into_tag_table(4, 't_four') == 4
    assert sql.insert_into_tag_table(3, 't_three', 10) == 3
    assert sql.insert_into_tag_table(None, 't_five') == 5
    with pytest.raises(IntegrityError):
        sql.insert_into_tag_table(3, 't_bad')

    # List
    tag_list = sql.get_tag_table_list()
    assert len(tag_list) == 5

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

    # Tag mappings
    tag_mapping = sql.get_tag_table_id_mapping()
    assert tag_mapping[1][MAP_TAG_NAME] == 't_one'
    assert tag_mapping[1][MAP_TAG_COUNT] == 0
    assert tag_mapping[2][MAP_TAG_NAME] == 't_two'
    assert tag_mapping[2][MAP_TAG_COUNT] == 0
    assert tag_mapping[3][MAP_TAG_NAME] == 't_three'
    assert tag_mapping[3][MAP_TAG_COUNT] == 10

    tag_mapping = sql.get_tag_table_name_mapping()
    assert tag_mapping['t_one'][MAP_TAG_ID] == 1
    assert tag_mapping['t_one'][MAP_TAG_COUNT] == 0
    assert tag_mapping['t_two'][MAP_TAG_ID] == 2
    assert tag_mapping['t_two'][MAP_TAG_COUNT] == 0
    assert tag_mapping['t_three'][MAP_TAG_ID] == 3
    assert tag_mapping['t_three'][MAP_TAG_COUNT] == 10


def test_field_table():
    sql = Sql()

    assert sql.insert_into_field_table(None, 'f_one', False) == 1
    assert sql.insert_into_field_table(None, 'f_two', True) == 2
    assert sql.insert_into_field_table(None, 'f_three', False, 10) == 3
    assert sql.insert_into_field_table(5, 'f_four', True) == 5

    with pytest.raises(IntegrityError):
        sql.insert_into_field_table(2, 'f_bad', True)

    field_list = sql.get_field_table_list()
    assert len(field_list) == 4

    # Lists
    assert field_list[0][INDEX_ID] == 1
    assert field_list[0][INDEX_FIELD_TABLE_NAME] == 'f_one'
    assert field_list[0][INDEX_FIELD_TABLE_SENSITIVE] is False
    assert field_list[0][INDEX_FIELD_TABLE_COUNT] == 0
    assert field_list[1][INDEX_ID] == 2
    assert field_list[1][INDEX_FIELD_TABLE_NAME] == 'f_two'
    assert field_list[1][INDEX_FIELD_TABLE_SENSITIVE] is True
    assert field_list[1][INDEX_FIELD_TABLE_COUNT] == 0
    assert field_list[2][INDEX_ID] == 3
    assert field_list[2][INDEX_FIELD_TABLE_NAME] == 'f_three'
    assert field_list[2][INDEX_FIELD_TABLE_SENSITIVE] is False
    assert field_list[2][INDEX_FIELD_TABLE_COUNT] == 10
    assert field_list[3][INDEX_ID] == 5
    assert field_list[3][INDEX_FIELD_TABLE_NAME] == 'f_four'
    assert field_list[3][INDEX_FIELD_TABLE_SENSITIVE] is True
    assert field_list[3][INDEX_FIELD_TABLE_COUNT] == 0

    # field mappings
    field_mapping = sql.get_field_table_id_mapping()
    assert field_mapping[1][MAP_FIELD_NAME] == 'f_one'
    assert field_mapping[1][MAP_FIELD_SENSITIVE] is True
    assert field_mapping[1][MAP_FIELD_COUNT] == 0
    assert field_mapping[2][MAP_FIELD_NAME] == 'f_two'
    assert field_mapping[1][MAP_FIELD_SENSITIVE] is True
    assert field_mapping[2][MAP_FIELD_COUNT] == 0
    assert field_mapping[3][MAP_FIELD_NAME] == 'f_three'
    assert field_mapping[1][MAP_FIELD_SENSITIVE] is True
    assert field_mapping[3][MAP_FIELD_COUNT] == 10

    field_mapping = sql.get_field_table_name_mapping()
    assert field_mapping['f_one'][MAP_TAG_ID] == 1
    assert field_mapping['f_one'][MAP_FIELD_SENSITIVE] is True
    assert field_mapping['f_one'][MAP_FIELD_COUNT] == 0
    assert field_mapping['f_two'][MAP_TAG_ID] == 2
    assert field_mapping['f_one'][MAP_FIELD_SENSITIVE] is False
    assert field_mapping['f_two'][MAP_FIELD_COUNT] == 0
    assert field_mapping['f_three'][MAP_TAG_ID] == 3
    assert field_mapping['f_one'][MAP_FIELD_SENSITIVE] is True
    assert field_mapping['f_three'][MAP_FIELD_COUNT] == 10


if __name__ == '__main__':
    test_tag_table()
    test_field_table()
