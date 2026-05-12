from web3 import Web3
from decimal import Decimal, getcontext

getcontext().prec = 80


# ========== 配置 ==========

RPC = "https://bsc-dataseed.binance.org/"

WALLET = Web3.to_checksum_address("Your's wallet address.")


MASTERCHEF_V3 = Web3.to_checksum_address(
    "0x556B9306565093C855AEA9AE92A594704c2Cd59e"
)

POSITION_MANAGER = Web3.to_checksum_address(
    "0x46A15B0b27311cedF172AB29E4f4766fbE7F4364"
)

FACTORY = Web3.to_checksum_address(
    "0x0BFbCF9fa4f9C56B0F40a671Ad40E0805A091865"
)


# ========== 初始化 ==========

w3 = Web3(Web3.HTTPProvider(RPC))


# ========== ABI ==========

MC_ABI = [
    {
        "name":"balanceOf",
        "inputs":[{"name":"user","type":"address"}],
        "outputs":[{"type":"uint256"}],
        "stateMutability":"view",
        "type":"function"
    },
    {
        "name":"tokenOfOwnerByIndex",
        "inputs":[
            {"name":"user","type":"address"},
            {"name":"index","type":"uint256"}
        ],
        "outputs":[{"type":"uint256"}],
        "stateMutability":"view",
        "type":"function"
    }
]


PM_ABI = [
    {
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
    }
]


# PancakeSwap v3 正确 slot0 ABI
POOL_ABI = [
    {
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
    }
]


FACTORY_ABI = [
    {
        "name":"getPool",
        "inputs":[
            {"type":"address"},
            {"type":"address"},
            {"type":"uint24"}
        ],
        "outputs":[{"type":"address"}],
        "stateMutability":"view",
        "type":"function"
    }
]


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


# ========== 合约实例 ==========

mc = w3.eth.contract(address=MASTERCHEF_V3, abi=MC_ABI)
pm = w3.eth.contract(address=POSITION_MANAGER, abi=PM_ABI)
factory = w3.eth.contract(address=FACTORY, abi=FACTORY_ABI)


# ========== 数学函数 ==========

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

    try:
        symbol = c.functions.symbol().call()
    except:
        symbol = "UNKNOWN"

    try:
        decimals = c.functions.decimals().call()
    except:
        decimals = 18

    return symbol, decimals


# ========== 主逻辑 ==========

def main():

    print("")
    print("正在查询 PancakeSwap v3 LP...")
    print("")

    count = mc.functions.balanceOf(WALLET).call()

    print("质押NFT数量:", count)
    print("")

    if count == 0:
        print("没有发现质押LP")
        return


    for i in range(count):

        tokenId = mc.functions.tokenOfOwnerByIndex(
            WALLET, i
        ).call()

        pos = pm.functions.positions(tokenId).call()

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


        if pool_addr == "0x0000000000000000000000000000000000000000":

            print("NFT ID:", tokenId)
            print("池不存在")
            print("")
            continue


        pool = w3.eth.contract(address=pool_addr, abi=POOL_ABI)


        try:
            slot0 = pool.functions.slot0().call()
        except Exception as e:

            print("NFT ID:", tokenId)
            print("slot0读取失败")
            print("")
            continue


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


        print("NFT ID:", tokenId)
        print(f"{symbol0}: {amount0:.10f}")
        print(f"{symbol1}: {amount1:.10f}")
        print("")


# ========== 启动 ==========

if __name__ == "__main__":
    main()

