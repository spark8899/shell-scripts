# pip3 install TonTools

import asyncio, pprint
from TonTools import TonCenterClient, Wallet

API_KEY = 'ton_center_api_key'
secret_key = "your secret key here"
recipient_address = 'recipient address here'
amount = 0.1

async def test_balance(API_KEY, MNEMONICS, recipient_address, amount):
    client = TonCenterClient(key=API_KEY, orbs_access=True, testnet=True)
    my_wallet = Wallet(provider=client, mnemonics=MNEMONICS, version="v4r2")
    balance = await my_wallet.get_balance()
    pprint.pprint(f"{my_wallet.address}: {balance / 10**9}")
    state = await my_wallet.get_state()
    if state != 'active':
        await my_wallet.deploy()
    await my_wallet.transfer_ton(destination_address=recipient_address, amount=amount, message='test')
    trs = await my_wallet.get_transactions()
    trs.reverse()
    for i in trs:
        if len(i.out_msgs) == 0:
            pprint.pprint(i.in_msg.to_dict())
        else:
            pprint.pprint(i.out_msgs[0].to_dict())

if __name__ == '__main__':
    MNEMONICS = secret_key.split()
    asyncio.run(test_balance(API_KEY, MNEMONICS, recipient_address, amount))
