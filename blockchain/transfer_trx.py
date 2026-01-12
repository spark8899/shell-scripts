# pip3 install tronpy

from tronpy import Tron
from tronpy.keys import PrivateKey

# create tron client.
client = Tron(network='nile')

# create tron account
private_key = "YOUR_PRIVATE_KEY"[2:]
priv_key = PrivateKey.fromhex(private_key)
tron_account = client.generate_address(priv_key)

# query balance
balance = client.get_account(tron_account['base58check_address']).get('balance', 0)
trx_balance = balance / 1_000_000
print(f"addr: {tron_account['base58check_address']} amount: {trx_balance} TRX")

# Set the amount of TRX to send and the destination address
to_address = "RECIPIENT_TRON_ADDRESS"
amount = 10 * 10**6

# Create a transaction
txn = client.trx.transfer(tron_account['base58check_address'], to_address, amount).build().sign(priv_key)

# Sending transactions
result = txn.broadcast().wait()
print("Trading Results:", result)
