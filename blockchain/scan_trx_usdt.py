#!/bin/env python3

import requests, json, sys, time

user_addr = 'TTNQi2Kbek6cvR6eEAVemoYpv1D9NZwmmD'

rpc = "https://api.trongrid.io"
usdt_address = 'TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t'

def call_balance(addr_id, address):
    url = "%s/%s/%s" % (rpc, "v1/accounts", address)
    headers = {"accept": "application/json", "content-type": "application/json"}
    response = requests.get(url, headers=headers)
    data = response.json()['data']
    if len(data) == 1:
        trx_balance = float(data[0]['balance']) / 10 ** 6
        usdt_balance = 0
        trc20 = data[0]['trc20']
        if len(trc20) > 0:
            for kv in trc20:
                if usdt_address in kv:
                    usdt_balance = float(kv[usdt_address]) / 10 ** 6
        print("%s,%s,%s TRX,%s USDT" % (addr_id, address, trx_balance, usdt_balance))

def main():
    #call_balance(user_addr)

    with open('address.csv', 'r') as f:
        lines = f.readlines()
        for i in lines:
            addr_id = i.split(',')[0]
            trx_addr = i.split(',')[3]
            call_balance(addr_id, trx_addr)
            time.sleep(5)

if __name__ == '__main__':
    print("start...")
    main()
    print("end.....")
