import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet

# Character encoding
CHARACTER_ENCODING = 'utf-8'


class Crypt:

    def __init__(self, password: str):
        """
        Implement data encryption and decryption
        :param password:
        """
        self.key = self.generate_crypt_key(password)

    @staticmethod
    def generate_crypt_key(password: str) -> Fernet:
        """
        Generate a Fernet key from a string password
        The salt should be fixed to encrypt/decrypt consistently
        :param password: password
        :return: key
        """
        password_bytes = password.encode(CHARACTER_ENCODING)
        salt = b'TDkmQ2TyV6HRw7pW'
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA512(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        return Fernet(base64.urlsafe_b64encode(kdf.derive(bytes(password_bytes))))

    def encrypt_str2byte(self, data: str) -> bytes:
        """
        Encrypt string data message into bytes
        :param data: data to encrypt
        :return: encrypted message
        """
        return self.key.encrypt(data.encode(CHARACTER_ENCODING))

    def encrypt_str2str(self, data: str) -> str:
        """
        Encrypt string data message into string
        :param data: data to encrypt
        :return: encrypted message
        """
        return self.key.encrypt(data.encode(CHARACTER_ENCODING)).decode(CHARACTER_ENCODING)

    def decrypt_byte2str(self, data: bytes) -> str:
        """
        Decrypt byte data message into string
        :param data: data to decrypt
        :return: decrypted data
        """
        return self.key.decrypt(data).decode(CHARACTER_ENCODING)

    def decrypt_str2str(self, data: str) -> str:
        """
        Decrypt string data message into string
        :param data: data to decrypt
        :return: decrypted data
        """
        return self.key.decrypt(data.encode(CHARACTER_ENCODING)).decode(CHARACTER_ENCODING)

    @staticmethod
    def dump(data: str | bytes):
        print(type(data), '[' + str(data) + ']')


if __name__ == '__main__':
    c = Crypt('test')
    m_in = 'This is a text string'

    m_enc = c.encrypt_str2byte(m_in)
    c.dump(m_enc)
    m_dec = c.decrypt_byte2str(m_enc)
    c.dump(m_dec)
    assert m_in == m_dec

    m_enc = c.encrypt_str2str(m_in)
    c.dump(m_enc)
    m_dec = c.decrypt_str2str(m_enc)
    c.dump(m_dec)
    assert m_in == m_dec
