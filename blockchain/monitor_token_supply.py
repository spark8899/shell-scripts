import json, sys
from web3 import Web3

RPC_URL = "https://bsc-dataseed.binance.org/"
MULTICALL3 = "0xcA11bde05977b3631167028862bE2a173976CA11"

# 静态元数据直接配好，避免重复打 RPC 查 symbol/decimals
TOKENS = [
    {"addr": "0x55d398326f99059fF775485246999027B3197955", "symbol": "USDT", "decimals": 18},
    # {"addr": "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c", "symbol": "WBNB", "decimals": 18},
]

MC3_ABI = json.loads('[{"inputs":[{"components":[{"name":"target","type":"address"},{"name":"allowFailure","type":"bool"},{"name":"callData","type":"bytes"}],"name":"calls","type":"tuple[]"}],"name":"aggregate3","outputs":[{"components":[{"name":"success","type":"bool"},{"name":"returnData","type":"bytes"}],"name":"returnData","type":"tuple[]"}],"stateMutability":"view","type":"function"}]')
ERC20_ABI = json.loads('[{"name":"totalSupply","type":"function","inputs":[],"outputs":[{"type":"uint256"}]}]')

w3 = Web3(Web3.HTTPProvider(RPC_URL))
if not w3.is_connected():
    sys.exit("Error: RPC offline")

mc = w3.eth.contract(address=MULTICALL3, abi=MC3_ABI)
calldata = w3.eth.contract(abi=ERC20_ABI).encode_abi("totalSupply", args=[])

calls = [{"target": Web3.to_checksum_address(t["addr"]), "allowFailure": True, "callData": calldata} for t in TOKENS]
try:
    results = mc.functions.aggregate3(calls).call()
except Exception as e:
    sys.exit(f"Multicall failed: {e}")

metrics = []
for t, (ok, data) in zip(TOKENS, results):
    if not ok or not data:
        continue
    supply = w3.codec.decode(["uint256"], data)[0] / 10 ** t["decimals"]
    addr = Web3.to_checksum_address(t["addr"])
    metrics.append(f'token_total_supply{{network="bsc", address="{addr}", symbol="{t["symbol"]}"}} {supply:.4f}')

if metrics:
    print("# HELP token_total_supply Total supply of the token\n# TYPE token_total_supply gauge")
    print("\n".join(metrics))
