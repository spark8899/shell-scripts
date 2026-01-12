# pip3 install bitcoinlib

from bitcoinlib.wallets import Wallet
from bitcoinlib.keys import Key

# Set up your private key
private_key = 'your private key'[2:]

# Create a key object from a private key
key = Key(private_key)

# Create a wallet object
# wallet = Wallet.create('MyTestNetWallet', keys=key, network='testnet')

# Load an existing wallet
wallet_name = 'MyTestNetWallet'
wallet = Wallet('MyTestNetWallet')

wallet.scan()
wallet.info()

# Print wallet address
print(f"Wallet Address: {wallet.get_key().address}")

# Check balance
balance = wallet.balance()
print(f"Wallet Balance: {balance} BTC")

# Get unspent transaction outputs
utxos = wallet.utxos()
print(f"Unspent transaction outputs: {utxos}")


# Set the receiving address and amount
recipient_address = 'recipient address'
amount_btc = 0.001

# Convert Bitcoin Amounts to Satoshis (satoshi)
amount_satoshi = int(amount_btc * 100_000_000)

# Create a transaction
tx = wallet.send_to(recipient_address, amount_satoshi)

# Print transaction information
print(f"Transaction Hash: {tx.txid}")
print(f"Transaction Details: {tx.as_dict()}")
