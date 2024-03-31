import string
import time
import re
import getpass
from datetime import datetime
from typing import Optional
from crypt import Crypt

# Flag to control the trace output
_trace_disable = True


def match_strings(pattern: str, s: str):
    """
    Check whether a regex pattern is contained into another string.
    The string matching is case insensitive.
    :param pattern: pattern to match
    :param s: string where to search
    :return: True in the string is
    """
    return True if re.search(pattern.lower(), s.lower()) else False


def trimmed_string(value: str) -> str:
    """
    Trim string. Provided for convenience.
    :param value: string value to trim
    :return: trimmed string
    """
    return value.strip()


def filter_control_characters(value: str) -> str:
    """
    Replace control characters from a string with a '<n>' equivalent.
    Used for debugging.
    :param value:
    :return: filtered value
    """
    o_str = ''
    for c in value:
        if c in string.printable and c not in string.whitespace or c == ' ':
            o_str += c
        else:
            o_str += '<' + str(ord(c)) + '>'
    return o_str


def get_timestamp() -> int:
    """
    Return a Unix timestamp, up to the second
    :return: time stamp
    """
    return int((datetime.now() - datetime(1970, 1, 1)).total_seconds())


def get_string_timestamp() -> str:
    """
    Return a time stamp in string format, up to the second
    :return: time stamp
    """
    return time.strftime("%Y%m%d%H%M%S", time.gmtime())


def timestamp_to_string(time_stamp: int, date_only=False) -> str:
    """
    Convert a Unix time stamp into a string, up to the second
    :param time_stamp: unix time stamp
    :return: string of the form 'YYYYMMDDHHMMSS' or 'YYYYMMDD'
    """
    try:
        format_string = '%d/%b/%Y' if date_only else '%d/%b/%Y %H:%M:%S'
        return datetime.utcfromtimestamp(time_stamp).strftime(format_string)
    except OverflowError:
        return 'overflow'


def get_password() -> str:
    """
    Read a password from the standard input.
    :return: password
    """
    return getpass.getpass('Password: ').strip()


def get_crypt_key() -> Crypt | None:
    """
    Read a password from the standard input and return the corresponding encryption key
    :return: encryption key, or None if no password
    """
    password = get_password()
    key = Crypt(password) if password else None
    del password
    return key


def sensitive_mark(sensitive: bool):
    """
    Return a label that can be used to mark sensitive information in reports
    :param sensitive: sensitive information?
    :return:
    """
    return '(*)' if sensitive else '   '


def print_line(width=70):
    """
    Print an horizontal line
    :param: with: line with in characters
    """
    print(horizontal_line(width=width))


def horizontal_line(width=40) -> str:
    """
    Return string containing a line drawn using the \u2015 unicode.
    :param width: line with (characters)
    :return: string with line characters
    """
    return u'\u2015' * width


def trace_toggle(disable_value: Optional[bool] = None):
    """
    Toggle the trace disable flag (used for debugging)
    :param disable_value: value to force trace flag
    :return:
    """
    global _trace_disable
    _trace_disable = not _trace_disable if disable_value is None else disable_value


def trace(label: str, *args):
    """
    Trace program execution (used for debugging)
    :param label: label
    :param args: arguments
    :return:
    """
    if _trace_disable:
        return
    if args:
        print(f'TRACE: {label}: ' + str([f'{x}' for x in args]))
    else:
        print(f'TRACE: {label}')


def error(message: str, *args):
    """
    Report an error
    :param message: error message
    :param args: arguments
    """
    arg_msg = ''
    if args:
        for arg in args:
            if isinstance(arg, Exception):
                arg_msg += f' {repr(arg)}'
            else:
                arg_msg += f' {str(arg)}'
    print(f'Error: {message}{arg_msg}')


def confirm(prompt: str) -> bool:
    """
    Prompt the user for confirmation
    :param prompt: prompt text
    :return: True if the user answered 'yes', False otherwise
    """
    print(prompt)
    answer = input('Do you want to proceed (yes/no)? ')
    return answer == 'yes'


if __name__ == '__main__':
    pass
