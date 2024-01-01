from utils import match_strings, trimmed_string, filter_control_characters
from utils import get_timestamp, get_string_timestamp, timestamp_to_string


def test_trimmed_string():
    s = 'This is a text'
    assert trimmed_string('   ' + s + '   ') == s


def test_match_strings():
    assert match_strings('one', 'two') is False
    assert match_strings('is', 'This is a string') is True
    assert match_strings('The.story', 'The story of') is True


def test_filter_control_characters():
    s = '\t\ttext\n\r'
    assert filter_control_characters(s) == '<9><9>text<10><13>'


def test_time_stamp():
    assert isinstance(get_timestamp(), int)
    assert isinstance(get_string_timestamp(), str)
    assert timestamp_to_string(1695219467) == '20/Sep/2023 14:17:47'


if __name__ == '__main__':
    test_trimmed_string()
    test_match_strings()
    test_filter_control_characters()
    test_time_stamp()
