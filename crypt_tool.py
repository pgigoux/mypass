#!/usr/bin/env python
"""
Simple program to quickly encrypt and decrypt strings. Used during software validation.
"""
import argparse
from utils import get_crypt_key

if __name__ == '__main__':

    # Process command line arguments
    parser = argparse.ArgumentParser()

    parser.add_argument(dest='input',
                        action='store',
                        type=str,
                        default='',
                        help='Input string')

    parser.add_argument('-d', '--decrypt',
                        dest='decrypt',
                        action='store_true',
                        default=False,
                        help='Decrypt string? [default=False]')

    parser.add_argument('-s', '--salt',
                        dest='salt',
                        action='store',
                        type=str,
                        default='',
                        help='encryption salt [default=blank]')

    args = parser.parse_args()

    # Initialize encryption/decryption with password from user
    c = get_crypt_key(input_salt=args.salt)

    # Decryption is expected to fail with ill-formed encrypted strings or password mismatch
    if args.decrypt:
        try:
            print(f'[{c.decrypt_str2str(args.input)}]')
        except Exception as e:
            print('decryption failed', e)
    else:
        print(f'[{c.encrypt_str2str(args.input)}]')
