#!/bin/env python3
# pip3 install base58 ecdsa pycryptodome

import base58, ecdsa
from Crypto.Hash import keccak


def hex_to_TRON_ADDR(key_string):

    keybytes = bytes.fromhex(key_string)

    sk = ecdsa.SigningKey.from_string(keybytes, curve=ecdsa.SECP256k1)
    key = sk.get_verifying_key()
    KEY = key.to_string()
    Keccak = keccak.new(digest_bits=256)
    Keccak.update(KEY)
    pub_key = Keccak.digest()
    primitive_addr = b'\x41' + pub_key[-20:]
    # 0 (zero), O (capital o), I (capital i) and l (lower case L)
    addr = base58.b58encode_check(primitive_addr)
    return addr.decode()

def main():
    key_string = "63e21d10fd50155dbba0e7d3f7431a400b84b4c2ac1ee38872f82448fe3ecfb9"
    address = hex_to_TRON_ADDR(key_string)
    print(address)

if __name__ == '__main__':
    main()
