#!/usr/bin/env python3
#_*_coding:utf-8_*_
# crontab
# */5 * * * * /root/tools/balance_monitor.py > /dev/null 2>&1
from web3 import Web3, HTTPProvider
import json, requests, time

rpc = 'https://bsc-dataseed.binance.org/'
WX_KEY = 'aabbccd-2838-fjkk-aabb-34553334334'
TELBOT_ID = 'bot72352429934:aabbccddeeffggwwggjjkk'
CHAT_ID = '-8883994883999'
localtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
m3_ADDRESS = Web3.to_checksum_address('0xaksdjbbccddkekfejjjj')

m4_ADDRESS = Web3.to_checksum_address('0xiifjkslldkkdfjjegj234jkj')
m4_ABI = json.loads('[{"inputs":[{"internalType":"string","name":"_name","type":"string"},{"internalType":"string","name":"_symbol","type":"string"},{"internalType":"address","name":"_fundAddress","type":"address"},{"internalType":"uint256","name":"_mintAmount","type":"uint256"}],"stateMutability":"nonpayable","type":"constructor"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"owner","type":"address"},{"indexed":true,"internalType":"address","name":"spender","type":"address"},{"indexed":false,"internalType":"uint256","name":"value","type":"uint256"}],"name":"Approval","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"previousOwner","type":"address"},{"indexed":true,"internalType":"address","name":"newOwner","type":"address"}],"name":"OwnershipTransferred","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"from","type":"address"},{"indexed":true,"internalType":"address","name":"to","type":"address"},{"indexed":false,"internalType":"uint256","name":"value","type":"uint256"}],"name":"Transfer","type":"event"},{"inputs":[{"internalType":"address","name":"_minter","type":"address"}],"name":"addMinter","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"owner","type":"address"},{"internalType":"address","name":"spender","type":"address"}],"name":"allowance","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"approve","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"account","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"burn","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"subtractedValue","type":"uint256"}],"name":"decreaseAllowance","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"_minter","type":"address"}],"name":"deleteMinter","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"addedValue","type":"uint256"}],"name":"increaseAllowance","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"_minter","type":"address"}],"name":"isMinter","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"account","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"mint","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"name","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"owner","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"renounceOwnership","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"symbol","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"totalSupply","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"transfer","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"from","type":"address"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"transferFrom","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"newOwner","type":"address"}],"name":"transferOwnership","outputs":[],"stateMutability":"nonpayable","type":"function"}]')

w3 = Web3(HTTPProvider(rpc))
m4_CONTRACT = w3.eth.contract(address=m4_ADDRESS, abi=m4_ABI)

def send_wx(text):
    url = 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=%s' % WX_KEY
    headers = {'Content-type': 'application/json', 'Accept': 'application/json'}
    content = {"msgtype" : "markdown", "markdown": {"content": text } }
    requests.post(url, data=json.dumps(content),  headers=headers)

def send_tel(telbot_id=TELBOT_ID, chat_id=CHAT_ID, text='', parse_mode="markdown"):
    url = "https://api.telegram.org/%s/sendMessage" % telbot_id
    headers = {'Content-type': 'application/json', 'Accept': 'application/json'}
    content = {"chat_id": chat_id, "text": text, "parse_mode": parse_mode}
    requests.post(url, data=json.dumps(content),  headers=headers)

def getBalanceInfo(address):
    ainfo = m4_CONTRACT.functions.getBalance(address).call()
    return {"balance": abs(ainfo[0])}

def main():
    print("query balance..")
    check_balance = 50000
    display_balance = "%dw" % (check_balance / 10000)
    balance_info = getBalanceInfo(m3_ADDRESS)
    a01 = balance_info['balance'] / 10 ** 18
    print("balance: %.2f" % a01)
    if a01 < check_balance:
        send_wx("Bot: balance lower")
        send_tel(text="Bot: balance less %s, value: %.2f" % (display_balance, a01))
    print(localtime[11:16])
    if localtime[11:16] == "01:25":
        send_wx("Bot: balance: %.2f" % a01)
        send_tel(text="Bot: balance: %.2f" % a01)

if __name__ == '__main__':
    print("process start...")
    main()
    print("process end.....")
