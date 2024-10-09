# pip3 install web3
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware

# addr and key
sender_address = "your address"
private_key = "your private key"
recipient_address = "recipient address"

# connect bsc test
bsc_testnet_url = "https://data-seed-prebsc-1-s1.binance.org:8545/"
bsc_chain_id = 97
web3 = Web3(Web3.HTTPProvider(bsc_testnet_url))

# add bsc PoA
web3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

# check connect
if web3.is_connected():
    print("Successfully connected to BSC testnet")
else:
    print("Failed to connect to BSC testnet")
    exit(1)

# usdt contract addr
usdt_address = "0x337610d27c682E347C9cD60BD4b3b107C9d34dDd"

# USDT ABI
usdt_abi = [
    {
        "constant": False,
        "inputs": [
            {"name": "_to", "type": "address"},
            {"name": "_value", "type": "uint256"}
        ],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    }
]

# Create a USDT contract instance
usdt_contract = web3.eth.contract(address=usdt_address, abi=usdt_abi)


# Transfer amount (the minimum unit of USDT is 18 decimal places on BSC)
amount = web3.to_wei(0.1, 'ether')  # 0.1 USDT

# Get the current nonce
nonce = web3.eth.get_transaction_count(sender_address)
print(nonce)

# Constructing a transaction
txn = usdt_contract.functions.transfer(recipient_address, amount).build_transaction({
    'chainId': bsc_chain_id,
    'gas': 100000,
    'gasPrice': web3.eth.gas_price,
    'nonce': nonce,
})

# Signing transactions
signed_txn = web3.eth.account.sign_transaction(txn, private_key)

# Sending transactions
tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)

# Waiting for the transaction to be confirmed
tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

print(f"Transaction successful with hash: {tx_hash.hex()}")
print(f"Transaction receipt: {tx_receipt}")
