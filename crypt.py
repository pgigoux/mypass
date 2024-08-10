import base64
from typing import Optional
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet

# Character encoding
CHARACTER_ENCODING = 'utf-8'

# Default salt
DEFAULT_SALT = b'TDkmQ2TyV6HRw7pW'


class Crypt:

    def __init__(self, password: str, salt=''):
        """
        Implement data encryption and decryption
        :param password:
        """
        self.key = self.generate_crypt_key(password, salt)

    def __str__(self):
        return f'{str(self.key)}'

    @staticmethod
    def generate_crypt_key(password: str, salt='') -> Fernet:
        """
        Generate a Fernet key from a string password
        The salt should be fixed to encrypt/decrypt consistently
        TODO: modify to use a variable salt value
        :param password: password
        :param salt: encryption salt
        :return: key
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA512(),
            length=32,
            salt=bytes(salt, CHARACTER_ENCODING) if len(salt) > 0 else DEFAULT_SALT,
            iterations=480000,
        )
        return Fernet(base64.urlsafe_b64encode(kdf.derive(password.encode(CHARACTER_ENCODING))))

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
    pass
