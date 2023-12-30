#!/usr/bin/env python
"""
Simple program to quickly encrypt and decrypt strings. Used during software validation.
"""
import argparse
from crypt import Crypt
from utils import get_password

if __name__ == '__main__':

    # Process command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('input', action='store', type=str, help='Input string')
    args = parser.parse_args()

    # Initialize encryption/decryption with password from user
    password = get_password()
    c = Crypt(password)

    # Try to encrypt/decrypt the string
    # Decryption is expected to fail with ill-formed encrypted strings
    print(f'enc: [{c.encrypt_str2str(args.input)}]')
    try:
        print(f'dec: [{c.decrypt_str2str(args.input)}]')
    except Exception as e:
        print('decryption failed', e)
