#!/bin/env python3

from web3 import Web3, HTTPProvider
import requests, json, sys, time

rpc = "https://cloudflare-eth.com"

web3 = Web3(HTTPProvider(rpc))
connect = web3.is_connected()
#print('web3 connect is', connect)

user_addr = '0x8b4Fc33dCD4d226D24B3C5149c7eea5363d0DC5C'

usdt_address = '0xdAC17F958D2ee523a2206206994597C13D831ec7'
usdt_abi = json.loads('[{"constant":true,"inputs":[{"name":"who","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"}]')
usdt_contract = web3.eth.contract(address=usdt_address, abi=usdt_abi)

def call_balance(addr_id, address):
    try:
        eth_balance = web3.from_wei(web3.eth.get_balance(address), "ether")
    except (RuntimeError, TypeError, NameError, ValueError):
        print("%s,%s get eth_balance error." % (addr_id, address))
        return

    try:
        usdt_balance = usdt_contract.functions.balanceOf(address).call() / 10 ** 6
    except (RuntimeError, TypeError, NameError, ValueError):
        print("%s,%s get usdt_balance error." % (addr_id, address))
        return
    print("%s,%s,%s ETH,%s USDT" % (addr_id, address, eth_balance, usdt_balance))

def main():
    #call_balance(user_addr)

    with open('address.csv', 'r') as f:
        lines = f.readlines()
        for i in lines:
            addr_id = i.split(',')[0]
            eth_addr = web3.to_checksum_address(i.split(',')[1])
            call_balance(addr_id, eth_addr)
            time.sleep(6)

if __name__ == '__main__':
    print("start...")
    main()
    print("end.....")
