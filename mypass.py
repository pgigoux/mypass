#!/usr/bin/env python
from cmd import Cmd
from parser import Parser


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
        pass

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
