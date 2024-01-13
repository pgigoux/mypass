#!/usr/bin/env python
from cmd import Cmd
from parser import Parser

HELP = """
db    <command_options>
tag   <command_options>
field <command_options>
item  <command_options>
"""

HELP_DB = """
create <file_name>
read [file_name]
write
export sql|json <file_name>
dump
report
"""

HELP_TAG = """
list
count
search <name>
add    <name>
delete <name>
rename <old_name> <new_name>
"""

HELP_FIELD = """
list
count
search <name>
add    <name>
delete <name>
rename <old_name> <new_name>
"""

HELP_ITEM = """
list
count
print  <item_id>
search <string> [-n] [-t] [-fn] [-fv] [--note]
delete <item_id>
copy   <item_id>
"""


class CommandInterpreter(Cmd):
    prompt = 'cmd> '
    intro = ''

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
