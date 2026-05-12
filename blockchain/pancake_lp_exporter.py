from web3 import Web3
from decimal import Decimal, getcontext

getcontext().prec = 80


# ========= 配置 =========

RPC = "https://bsc-dataseed.binance.org/"

NFT_IDS = [
    123456,
    # 添加更多 NFT ID
]


POSITION_MANAGER = Web3.to_checksum_address(
    "0x46A15B0b27311cedF172AB29E4f4766fbE7F4364"
)

FACTORY = Web3.to_checksum_address(
    "0x0BFbCF9fa4f9C56B0F40a671Ad40E0805A091865"
)


# ========= 初始化 =========

w3 = Web3(Web3.HTTPProvider(RPC))


# ========= ABI =========

PM_ABI = [{
    "name":"positions",
    "inputs":[{"name":"tokenId","type":"uint256"}],
    "outputs":[
        {"type":"uint96"},
        {"type":"address"},
        {"type":"address"},
        {"type":"address"},
        {"type":"uint24"},
        {"type":"int24"},
        {"type":"int24"},
        {"type":"uint128"},
        {"type":"uint256"},
        {"type":"uint256"},
        {"type":"uint128"},
        {"type":"uint128"}
    ],
    "stateMutability":"view",
    "type":"function"
}]


POOL_ABI = [{
    "name":"slot0",
    "inputs":[],
    "outputs":[
        {"type":"uint160"},
        {"type":"int24"},
        {"type":"uint16"},
        {"type":"uint16"},
        {"type":"uint16"},
        {"type":"uint32"},
        {"type":"bool"}
    ],
    "stateMutability":"view",
    "type":"function"
}]


FACTORY_ABI = [{
    "name":"getPool",
    "inputs":[
        {"type":"address"},
        {"type":"address"},
        {"type":"uint24"}
    ],
    "outputs":[{"type":"address"}],
    "stateMutability":"view",
    "type":"function"
}]


ERC20_ABI = [
    {
        "name":"symbol",
        "inputs":[],
        "outputs":[{"type":"string"}],
        "stateMutability":"view",
        "type":"function"
    },
    {
        "name":"decimals",
        "inputs":[],
        "outputs":[{"type":"uint8"}],
        "stateMutability":"view",
        "type":"function"
    }
]


pm = w3.eth.contract(address=POSITION_MANAGER, abi=PM_ABI)
factory = w3.eth.contract(address=FACTORY, abi=FACTORY_ABI)


# ========= 数学 =========

def sqrtPriceX96_to_decimal(v):
    return Decimal(v) / Decimal(2**96)


def tick_to_sqrtPrice(tick):
    return Decimal(1.0001) ** Decimal(tick/2)


def get_amounts(liquidity, sqrtPrice, sqrtLower, sqrtUpper):

    liquidity = Decimal(liquidity)

    if sqrtPrice <= sqrtLower:
        amount0 = liquidity * (sqrtUpper - sqrtLower) / (sqrtLower * sqrtUpper)
        amount1 = Decimal(0)

    elif sqrtPrice < sqrtUpper:
        amount0 = liquidity * (sqrtUpper - sqrtPrice) / (sqrtPrice * sqrtUpper)
        amount1 = liquidity * (sqrtPrice - sqrtLower)

    else:
        amount0 = Decimal(0)
        amount1 = liquidity * (sqrtUpper - sqrtLower)

    return amount0, amount1


def get_token_info(token):

    c = w3.eth.contract(address=token, abi=ERC20_ABI)

    symbol = c.functions.symbol().call()
    decimals = c.functions.decimals().call()

    return symbol, decimals


# ========= 输出 =========

print("# HELP pancake_lp_balance PancakeSwap LP token balance")
print("# TYPE pancake_lp_balance gauge")


for nft_id in NFT_IDS:

    try:

        pos = pm.functions.positions(nft_id).call()

        token0 = pos[2]
        token1 = pos[3]
        fee = pos[4]

        tickLower = pos[5]
        tickUpper = pos[6]
        liquidity = pos[7]

        symbol0, dec0 = get_token_info(token0)
        symbol1, dec1 = get_token_info(token1)

        pool_addr = factory.functions.getPool(
            token0,
            token1,
            fee
        ).call()

        pool = w3.eth.contract(address=pool_addr, abi=POOL_ABI)

        slot0 = pool.functions.slot0().call()

        sqrtPrice = sqrtPriceX96_to_decimal(slot0[0])

        sqrtLower = tick_to_sqrtPrice(tickLower)
        sqrtUpper = tick_to_sqrtPrice(tickUpper)

        amount0, amount1 = get_amounts(
            liquidity,
            sqrtPrice,
            sqrtLower,
            sqrtUpper
        )

        amount0 = amount0 / Decimal(10**dec0)
        amount1 = amount1 / Decimal(10**dec1)

        print(
            f'pancake_lp_balance{{nft_id="{nft_id}",token="{symbol0}"}} {float(amount0)}'
        )

        print(
            f'pancake_lp_balance{{nft_id="{nft_id}",token="{symbol1}"}} {float(amount1)}'
        )

    except Exception as e:

        print(
            f'# error nft_id="{nft_id}" {str(e)}'
        )

