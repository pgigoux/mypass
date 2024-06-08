#!/usr/bin/env python
from cmd import Cmd
from parser import Parser

HELP = """
db    <command_options>         Database commands
tag   <command_options>         Tag commands
field <command_options>         Field commands
item  <command_options>         Item command
trace                           Toggle code trace
"""

HELP_DB = """
create <file_name>              Create empty database
read [file_name]                Read database from file
write                           Write database
export sql|json <file_name>     Export database as sql or json
dump                            Dump database (debugging)
report                          Print database report (debugging)
"""

HELP_TAG = """
list                            List available tags
count                           Return number of tags
search <name>                   Search for a tag by name
add    <name>                   Add a new tag
delete <name>                   Delete an existing tag
rename <old_name> <new_name>    Rename an existing tag
"""

HELP_FIELD = """
list                            List available fields
count                           Return number of tags
search <name>                   Search for a field by name
add    <name>                   Add a new field
delete <name>                   Delete an existing field
rename <old_name> <new_name>    Rename an existing field
"""

HELP_ITEM = """
use    <item_id>                                    Set item id for tag/field/print operations
list                                                List available items
count                                               Return number of items
print  [item_id]                                    Print item contents
search <string> [-n] [-t] [-fn] [-fv] [-note]       Search for an item
delete <item_id>                                    Delete an existing item
copy   <item_id>                                    Copy/duplicate an item
add    [-n <string>] [-t tag] [-note <string>]      Add new item
update <item_id> [-n <string>] [-note <string>]     Update an existing item
tag    add|delete <tag_name>                        Add/delete item tag
field  add <field_name> <field_value>               Add item field
field  delete <field_id>                            Delete item field
field  update <field_id> [-fn <name>] [-fv <value>] Update item field
"""


class CommandInterpreter(Cmd):
    prompt = 'cmd> '
    intro = 'Welcome to mypass'

    def __init__(self, p: Parser):
        super().__init__()
        self.parser = p

    # ignore eof (ctrl-d)
    def do_EOF(self, _) -> bool:
        print('')
        return False

    # ignore empty lines
    def emptyline(self) -> bool:
        return False

    def do_help(self, topic: str):
        if topic == '':
            print(HELP)
        elif topic == 'db':
            print(HELP_DB)
        elif topic == 'tag':
            print(HELP_TAG)
        elif topic == 'field':
            print(HELP_FIELD)
        elif topic == 'item':
            print(HELP_ITEM)
        else:
            print(f'unknown {topic}')

    # Process command
    def default(self, command: str):
        self.parser.execute(command)

    def do_bye(self, _: str) -> bool:
        self.parser.quit(False)
        return True


if __name__ == '__main__':
    parser = Parser()
    ci = CommandInterpreter(parser)
    try:
        ci.cmdloop()
    except KeyboardInterrupt:
        parser.quit(True)
