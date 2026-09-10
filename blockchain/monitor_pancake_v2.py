import json, sys
from web3 import Web3

RPC_URL = "https://bsc-dataseed.binance.org/"
MULTICALL3 = "0xcA11bde05977b3631167028862bE2a173976CA11"

# 币对列表配置：建议直接配好 decimals，只需单次聚合查 reserves
POOLS = [
    {"addr": "0x16b9a82891338f9bA80E2D6970FddA79D1eb0daE", "s0": "CAKE", "d0": 18, "s1": "WBNB", "d1": 18},
    # {"addr": "0x...", "s0": "USDT", "d0": 18, "s1": "WBNB", "d1": 18},
]

MC3_ABI = json.loads('[{"inputs":[{"components":[{"name":"target","type":"address"},{"name":"allowFailure","type":"bool"},{"name":"callData","type":"bytes"}],"name":"calls","type":"tuple[]"}],"name":"aggregate3","outputs":[{"components":[{"name":"success","type":"bool"},{"name":"returnData","type":"bytes"}],"name":"returnData","type":"tuple[]"}],"stateMutability":"view","type":"function"}]')
PAIR_ABI = json.loads('[{"constant":true,"inputs":[],"name":"getReserves","outputs":[{"name":"_reserve0","type":"uint112"},{"name":"_reserve1","type":"uint112"},{"name":"_blockTimestampLast","type":"uint32"}],"type":"function"}]')

w3 = Web3(Web3.HTTPProvider(RPC_URL))
if not w3.is_connected():
    sys.exit("RPC offline")

mc_contract = w3.eth.contract(address=MULTICALL3, abi=MC3_ABI)
pair_dummy = w3.eth.contract(abi=PAIR_ABI)
reserves_calldata = pair_dummy.encode_abi("getReserves", args=[])

# 打包所有池子的 getReserves 请求
calls = [
    {"target": Web3.to_checksum_address(p["addr"]), "allowFailure": True, "callData": reserves_calldata}
    for p in POOLS
]

try:
    results = mc_contract.functions.aggregate3(calls).call()
except Exception as e:
    sys.exit(f"Multicall failed: {e}")

metrics = []
for p, (success, ret_bytes) in zip(POOLS, results):
    if not success or not ret_bytes:
        continue
    r0, r1, _ = w3.codec.decode(["uint112", "uint112", "uint32"], ret_bytes)
    pool_addr = Web3.to_checksum_address(p["addr"])
    metrics.append(f'pancakeswap_v2_reserve0{{pool="{pool_addr}", symbol="{p["s0"]}"}} {r0 / 10**p["d0"]:.6f}')
    metrics.append(f'pancakeswap_v2_reserve1{{pool="{pool_addr}", symbol="{p["s1"]}"}} {r1 / 10**p["d1"]:.6f}')

if metrics:
    print("# HELP pancakeswap_v2_reserve0 Actual reserve of token0\n# TYPE pancakeswap_v2_reserve0 gauge")
    print("# HELP pancakeswap_v2_reserve1 Actual reserve of token1\n# TYPE pancakeswap_v2_reserve1 gauge")
    print("\n".join(metrics))
