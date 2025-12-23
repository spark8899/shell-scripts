#!/usr/bin/env python3
# encoding: utf-8

from web3 import Web3

def string_to_bytes(message: str) -> str:
    """
    将字符串转换为 EVM 可用的 bytes (hex 字符串)
    """
    # 转成 UTF-8 bytes
    b = message.encode("utf-8")
    # 转 hex 字符串
    hex_data = Web3.to_hex(b)
    return hex_data

if __name__ == "__main__":
    msg = "2025-12-18 20:20:20(UTC+8) I'm here."
    hex_data = string_to_bytes(msg)
    print(f"Message: {msg}")
    print(f"Data (hex for MultiSig.data): {hex_data}")
