#!/usr/bin/env python
"""
Program used to import a password database exported from Enpass in json format
It generates an output database with much less information.

The input file is dictionary containing two lists: folders and items. Each folder is in turn a dictionary
of string values. Each item is a dictionary containing numbers, strings, lists of strings and list of
sub-dictionaries. Only a few elements in the items are really relevant.

{
    "folders": [
        {
            "icon": "1008",
            "parent_uuid": "",
            "title": "Business",
            "updated_at": 1527696441,
            "uuid": "f7a59f9c-c7c5-409f-8e3b-3ce4ea57519a"
        },
        ... more folders
    ]
    "items": [
        {
            "archived": 0,
            "auto_submit": 1,
            "category": "misc",
            "createdAt": 1527696211,
            "favorite": 0,
            "fields": [
                {
                    "deleted": 0,
                    "label": "Access number",
                    "order": 1,
                    "sensitive": 0,
                    "type": "numeric",
                    "uid": 0,
                    "updated_at": 1527696211,
                    "value": "",
                    "value_updated_at": 1527696211
                },
                {
                    "deleted": 0,
                    "label": "PIN",
                    "order": 2,
                    "sensitive": 1,
                    "type": "pin",
                    "uid": 1,
                    "updated_at": 1527696211,
                    "value": "0000",
                    "value_updated_at": 1527696211
                }
            ],
            "folders": [
                "f7a59f9c-c7c5-409f-8e3b-3ce4ea57519a"
            ],
            "icon": {
                "fav": "",
                "image": {
                    "file": "misc/calling"
                },
                "type": 1,
                "uuid": ""
            },
            "note": "",
            "subtitle": "",
            "template_type": "misc.voicemail",
            "title": "Some company",
            "trashed": 0,
            "updated_at": 1527696294,
            "uuid": "2d4dc0e9-b0df-4197-9c93-cbf422688520"
        },
        ... more items
    ]
}
"""
import json
import argparse
from crypt import Crypt
from db import Database, DEFAULT_DATABASE_NAME
from utils import get_crypt_key, trimmed_string, trace, trace_toggle

# Files used to save tables into separate files
FIELD_FILE_NAME = 'fields.csv'
TAG_FILE_NAME = 'tags.csv'

# Default tag for those items that do not have a tag/folder defined
# The uid value is completely arbitrary, but follows the format of other uid for consistency
TAG_DEFAULT_UID = '00000000-0000-0000-0000-000000000000'
TAG_DEFAULT_NAME = 'default'


def process_field(field: dict) -> tuple:
    """
    Process field contents.
    Ignore fields that have no value or that are of no interest
    Rename fields and make sure the sensitive flag is set for certain fields
    :param field: field contents
    :return: field name, value and sensitive flag
    :raise: ValueError if the field contents is empty or of no interest
    """
    trace('process fields', len(field))
    # Extract the field name, value and sensitive flag
    f_name = trimmed_string(field['label'])
    f_sensitive = True if field['sensitive'] == 1 else False
    f_value = trimmed_string(field['value'])

    # Ignore some fields or empty values
    if not f_value:
        raise ValueError(f'empty field {f_name}')
    if f_name in ['508', 'If lost, call']:
        raise ValueError(f'ignored name {f_name}')

    # Fix naming problems and sensitive flags
    if f_name == 'Add. password':
        f_name = 'Additional password'
    elif f_name == 'Handset Model':
        f_name = 'Model'
    elif f_name == 'Username':
        f_name = "User name"
    elif f_name in ['Consumer ID', 'Consumer Id', 'Customer id']:
        f_name = 'Customer Id'
    elif f_name == 'Host Name':
        f_name = 'Host name'
    elif f_name == 'E-mail':
        f_name = 'Email'
    elif f_name in ['Expiry date', 'Expiration date', 'Valid']:
        f_name = 'Valid until'
    elif f_name == 'MAC/Airport #':
        f_name = 'MAC'
    elif f_name == 'Server/IP address':
        f_name = 'IP address'
    elif f_name == 'Website':
        f_name = 'URL'
    elif 'Serial' in f_name:
        f_name = 'Serial number'
        f_sensitive = True
    elif f_name == 'Login name':
        f_name = 'Login'
    elif f_name == 'ID number':
        f_name = 'ID'
    elif 'Security Answer' in f_name:
        f_name = f_name.replace('Security Answer', 'Security answer')
        f_sensitive = True
    elif 'Securiry' in f_name:
        f_name = f_name.replace('Securiry', 'Security')
    elif 'Security answer' in f_name:
        f_sensitive = True

    # Do not allow blanks in field names
    f_name = f_name.replace(' ', '_')

    return f_name.lower(), f_value, f_sensitive


def process_tag(name: str) -> str:
    """
    Rename old tag name into a new one.
    It is possible to rename more than one old name into a new one.
    :param name: old name
    :return: new name
    """
    trace('process_tag', name)
    if name == 'Bank and Cards':
        name = 'Finance'
    elif name == 'Education and blogs':
        name = 'Education'
    elif name == 'Other Cards':
        name = 'Other'
    elif name in ['AURA', 'Gemini']:  # duplicate
        name = 'Work'
    return name.lower()


def save_tables(db: Database):
    """
    Save the field and tag tables to csv files
    :param db: database
    """
    trace('save_tables', db)
    try:
        db.tag_table_export(TAG_FILE_NAME)
        db.field_table_export(FIELD_FILE_NAME)
    except Exception as ex:
        print('Failed to save tables', ex)


def import_tags(db: Database, folder_list: list) -> dict:
    """
    :param db: database
    :param folder_list: list of folders/tags
    :return: dictionary with tag mapping
    """
    trace('import_tags', db, len(folder_list))

    # Create default tag for items that have no folder
    tag_dict = {TAG_DEFAULT_UID: db.sql.insert_into_tag_table(None, TAG_DEFAULT_NAME)}

    # Create a dictionary to store the mapping between the new tags names and the new tag ids.
    # This is needed to avoid duplication because some of the old tag names are mapped into
    # a single new name.
    tag_id_dict = {}
    for folder in folder_list:
        t_name = process_tag(folder['title'])
        if t_name not in tag_id_dict:
            tag_id_dict[t_name] = db.sql.insert_into_tag_table(None, t_name)

    # Iterate over all the folder definitions and create the dictionary with a
    # mapping between the uid from the input database and the id that will be
    # used in the new database.
    for folder in folder_list:
        tag_dict[folder['uuid']] = tag_id_dict[process_tag(folder['title'])]

    return tag_dict


def import_fields(db: Database, item_list: list):
    """
    Create the field table from the field names in the database items
    :param db: database
    :param item_list: list of items
    """
    trace('import_fields', db, len(item_list))

    # Compile the list of all field names used in the database items
    # into a set to eliminate duplicates.
    # The fields that are not relevant are ignored at this point.
    field_set = set()
    for item in item_list:
        for field in item['fields']:
            try:
                f_name, _, f_sensitive = process_field(field)
                field_set.add((f_name, f_sensitive))
            except ValueError:
                pass

    # Insert fields in the field table
    for f_name, f_sensitive in field_set:
        db.sql.insert_into_field_table(None, f_name, f_sensitive)


def import_items(db: Database, item_list: list, tag_mapping: dict):
    """
    Import the items into the database. The tags are converted using the tag mapping.
    :param db: database
    :param item_list: list of items
    :param tag_mapping: tag mapping
    """
    trace('import_items', db, len(tag_mapping))

    field_mapping = db.sql.get_field_table_name_mapping()

    for item in item_list:

        # An item should be a dictionary
        assert isinstance(item, dict)

        # Initialize item data
        item_name = ''
        note = ''
        time_stamp = 0
        tag_list = []
        field_list = []

        # Loop over all items
        for key in item.keys():
            value = item[key]
            if key == 'title':
                item_name = trimmed_string(value)
            elif key == 'createdAt':
                time_stamp = int(trimmed_string(str(value)))
            elif key == 'note':
                note = value
            elif key == 'folders':  # list
                for folder in value:
                    tag_list.append(tag_mapping[folder])
            elif key == 'fields':  # list
                for field in value:
                    f_encrypted = False
                    try:
                        f_name, f_value, f_sensitive = process_field(field)
                        if f_sensitive and db.crypt_key is not None:
                            assert isinstance(db.crypt_key, Crypt)
                            f_value = db.crypt_key.encrypt_str2str(f_value)
                            f_encrypted = True
                        field_list.append((f_name, f_value, f_encrypted))
                    except ValueError:
                        # can be safely ignored
                        continue

        # Assign a default tag list for items with no tag
        if len(tag_list) == 0:
            tag_list.append(tag_mapping[TAG_DEFAULT_UID])

        # Insert the item into the database
        # print('**', tag_list)
        item_id = db.sql.insert_into_items(None, item_name, int(time_stamp), note)
        for t_id in tag_list:
            db.sql.insert_into_tags(None, item_id, t_id)
        for f_name, f_value, f_encrypted in field_list:
            f_id = field_mapping[f_name][0]
            db.sql.insert_into_fields(None, item_id, f_id, f_value, f_encrypted)


def import_database(input_file_name: str, output_file_name: str, crypt_key: Crypt, dump_database=False):
    """
    Import an Enpass database in json format
    :param input_file_name: input file name (json format)
    :param output_file_name: output file name
    :param crypt_key: key used to encrypt the output database
    :param dump_database: print the database to the terminal?
    """
    trace('import_database', input_file_name, output_file_name, crypt_key, dump_database)

    # Read the data from the json file
    with open(input_file_name, 'r') as f:
        json_data = json.load(f)
    f.close()
    assert isinstance(json_data, dict)

    # Import data into database
    db = Database(output_file_name, crypt_key=crypt_key)
    tag_mapping = import_tags(db, json_data['folders'])
    import_fields(db, json_data['items'])
    import_items(db, json_data['items'], tag_mapping)
    db.write()

    # Save the tag and field tables as csv for reference
    save_tables(db)

    # Dump the database to the terminal
    if dump_database:
        db.dump()

    db.close()


if __name__ == '__main__':
    # Testing
    # import_database('pdb.json', 'pw.db', None, dump_database=False)
    # exit(0);

    # Command line arguments
    parser = argparse.ArgumentParser(description='Import Enpass database')

    parser.add_argument('input_file',
                        action='store',
                        type=str,
                        help='Input file name in JSON format')

    parser.add_argument('-o', '--output',
                        dest='output_file',
                        action='store',
                        type=str,
                        default=DEFAULT_DATABASE_NAME,
                        help='Output database file')

    parser.add_argument('-s', '--salt',
                        dest='salt',
                        action='store',
                        type=str,
                        default='',
                        help='Encryption salt')

    parser.add_argument('-d',
                        dest='dump',
                        action='store_true',
                        default=False,
                        help='Print output database to stdout?')

    parser.add_argument('-t',
                        dest='trace',
                        action='store_true',
                        default=False,
                        help='trace program execution?')

    args = parser.parse_args()

    # Get the key to encrypt the output database
    encrypt_key = get_crypt_key(input_salt=args.salt)

    if args.trace:
        trace_toggle(False)

    # Import the data
    try:
        import_database(args.input_file, args.output_file, encrypt_key, dump_database=args.dump)
    except Exception as e:
        print(f'Error while importing file {e}')
