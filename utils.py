import os
import string
import time
import re
import getpass
import subprocess
import tempfile
from datetime import datetime
from typing import Optional
from dataclasses import dataclass
from crypt import Crypt


@dataclass
class Trace:
    """
    Class used to control code tracing without global variables
    """
    trace_flag = False


def match_strings(pattern: str, s: str):
    """
    Check whether a regex pattern is contained into another string.
    The string matching is case-insensitive.
    :param pattern: pattern to match
    :param s: string where to search
    :return: True in the string is
    """
    return re.search(pattern.lower(), s.lower()) is not None


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
    :param date_only: return date without time
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
    Print a horizontal line
    :param: with: line with in characters
    """
    print(horizontal_line(width=width))


def horizontal_line(width=40) -> str:
    """
    Return string containing a line drawn using the \u2015 unicode.
    :param width: line with (characters)
    :return: string with line characters
    """
    return '\u2015' * width


def trace_toggle(value: Optional[bool] = None):
    """
    Toggle the trace flag (used for debugging)
    :param value: value to force trace flag
    :return:
    """
    Trace.trace_flag = not Trace.trace_flag if value is None else value


def trace(label: str, *args):
    """
    Trace program execution (used for debugging)
    :param label: label
    :param args: arguments
    :return:
    """
    if Trace.trace_flag:
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
    print(answer == 'yes')
    return answer == 'yes'


def edit_text(text: str) -> str | None:
    """
    Edit text in a text editor
    The text editor to use is obtained from the EDITOR environment variable (default vim)
    :param text:
    :return: output text or None if an error occurred
    """
    # Create a temporary file with the text
    temp_file_name = tempfile.mktemp()
    try:
        f = open(temp_file_name, 'w')
        f.write(text)
        f.close()
    except OSError:
        return None

    # Edit the temporary file
    command = [os.environ.get('EDITOR', 'vim'), temp_file_name]
    try:
        subprocess.run(command, check=True, capture_output=False)
    except subprocess.CalledProcessError:
        return None

    # Read the file contents
    try:
        with open(temp_file_name, 'r') as f:
            new_text = f.read()
    except OSError:
        return None

    # Remove the temporary file
    try:
        os.remove(temp_file_name)
    except OSError:
        pass

    # Return the edited text
    return new_text.rstrip()


if __name__ == '__main__':
    pass
