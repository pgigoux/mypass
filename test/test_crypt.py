import os
from crypt import Crypt


def test_string_encryption():
    c = Crypt('password')

    m_in = 'this is a message'
    data = c.encrypt_str2str(m_in)
    assert isinstance(data, str)

    m_out = c.decrypt_str2str(data)
    assert isinstance(m_out, str)

    assert m_in == m_out


def test_byte_encryption():
    c = Crypt('password')

    m_in = 'this is a message'
    data = c.encrypt_str2byte(m_in)
    assert isinstance(data, bytes)

    m_out = c.decrypt_byte2str(data)
    assert isinstance(m_out, str)

    assert m_in == m_out


def test_file_encryption():
    c = Crypt('password')
    file_name = 'test_file.txt'
    m_in = 'This is a message'

    data = c.encrypt_str2byte(m_in)
    f = open(file_name, "wb")
    f.write(data)
    f.close()

    f = open(file_name, 'rb')
    data = f.read()
    m_out = c.decrypt_byte2str(data)
    f.close()

    assert m_in == m_out

    os.remove(file_name)
