#!/usr/bin/env python3
# pip3 install web3 eth-abi
from web3 import Web3
from eth_abi import decode


# 1. Configuration
RPC_URL = "https://bsc-dataseed.binance.org/"
W3 = Web3(Web3.HTTPProvider(RPC_URL))

MULTICALL_ADDR = W3.to_checksum_address("0xcA11bde05977b3631167028862bE2a173976CA11")
TOKEN_ADDR = W3.to_checksum_address("0x55d398326f99059fF775485246999027B3197955") # BSC USDT
DECIMALS = 18

TARGET_USERS = [
    "0x28C6c06298d514Db089934071355E5743bf21d60",
    "0x47ac0Fb4F2D84898e4D9E7b4DaB3C24507a6D503",
]

# 2. Minified ABIs (Added totalSupply)
ERC20_ABI = [
    {"inputs": [{"type": "address"}], "name": "balanceOf", "outputs": [{"type": "uint256"}], "type": "function"},
    {"inputs": [], "name": "totalSupply", "outputs": [{"type": "uint256"}], "type": "function"}
]
MULTICALL_ABI = [{"inputs": [{"type": "bool"}, {"components": [{"type": "address"}, {"type": "bytes"}], "type": "tuple[]"}], "name": "tryAggregate", "outputs": [{"components": [{"type": "bool"}, {"type": "bytes"}], "type": "tuple[]"}], "stateMutability": "view", "type": "function"}]

# 3. Setup Contracts
token_contract = W3.eth.contract(address=TOKEN_ADDR, abi=ERC20_ABI)
multicall_contract = W3.eth.contract(address=MULTICALL_ADDR, abi=MULTICALL_ABI)

def main():
    # 4. Fetch Total Supply
    total_supply_wei = token_contract.functions.totalSupply().call()
    total_supply = total_supply_wei / (10 ** DECIMALS)
    
    # 5. Prepare multicall payload
    calls = []
    for user in TARGET_USERS:
        user_addr = W3.to_checksum_address(user)
        call_data = token_contract.encode_abi("balanceOf", args=[user_addr])
        calls.append((TOKEN_ADDR, call_data))

    # 6. Execute tryAggregate
    try:
        results = multicall_contract.functions.tryAggregate(False, calls).call()
        
        # 7. Decode results and calculate sum
        print("--- Individual Balances ---")
        target_users_total = 0
        
        for i, (success, raw_data) in enumerate(results):
            user = TARGET_USERS[i]
            
            if success and raw_data and raw_data != b'':
                balance_wei = decode(['uint256'], raw_data)[0]
                actual_balance = balance_wei / (10 ** DECIMALS)
                target_users_total += actual_balance
                print(f"{user} : {actual_balance} USDT")
            else:
                print(f"{user} : Query Failed")
        
        # 8. Calculate and print final summary
        adjusted_supply = total_supply - target_users_total
        
        print("\n--- Summary ---")
        print(f"Total Supply     : {total_supply:,.2f} USDT")
        print(f"Excluded Targets : {target_users_total:,.2f} USDT")
        print(f"Adjusted Supply  : {adjusted_supply:,.2f} USDT")
                
    except Exception as e:
        print(f"Execution failed: {e}")

if __name__ == "__main__":
    main()
