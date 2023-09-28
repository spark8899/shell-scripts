#!/bin/env python3

import requests, json, sys, time

user_addr = 'f1c7aexi3kcradekkhxg7ybxxhj2g7o4pqpcj5cqa'

rpc = "https://api.filutils.com"

def call_balance(addr_id, address):
    url = "%s/%s/%s" % (rpc, "api/v2/actor", address)
    headers = {"accept": "application/json", "content-type": "application/json"}
    response = requests.get(url, headers=headers)
    data = response.json()['data']
    fil_balance = data['balance']
    print("%s,%s,%s" % (addr_id, address, fil_balance))

def main():
    #call_balance('0', user_addr)

    with open('address.csv', 'r') as f:
        lines = f.readlines()
        for i in lines:
            addr_id = i.split(',')[0]
            fil_addr = i.split(',')[2]
            call_balance(addr_id, fil_addr)
            time.sleep(5)

if __name__ == '__main__':
    print("start...")
    main()
    print("end.....")
