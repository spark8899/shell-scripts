import os
import requests
import pymysql
from web3 import Web3
from decimal import Decimal, getcontext
from dotenv import load_dotenv

# 初始化
getcontext().prec = 80
load_dotenv()

# ========= 配置 =========
RPC = os.getenv("RPC_URL")
TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")
w3 = Web3(Web3.HTTPProvider(RPC))

# 合约地址
POSITION_MANAGER = Web3.to_checksum_address("0x46A15B0b27311cedF172AB29E4f4766fbE7F4364")
FACTORY = Web3.to_checksum_address("0x0BFbCF9fa4f9C56B0F40a671Ad40E0805A091865")

# ABI (简写形式)
ERC20_ABI = [{"name":"balanceOf","inputs":[{"name":"account","type":"address"}],"outputs":[{"type":"uint256"}],"stateMutability":"view","type":"function"},{"name":"decimals","inputs":[],"outputs":[{"type":"uint8"}],"stateMutability":"view","type":"function"},{"name":"symbol","inputs":[],"outputs":[{"type":"string"}],"stateMutability":"view","type":"function"}]
PM_ABI = [{"name":"positions","inputs":[{"name":"tokenId","type":"uint256"}],"outputs":[{"type":"uint96"},{"type":"address"},{"type":"address"},{"type":"address"},{"type":"uint24"},{"type":"int24"},{"type":"int24"},{"type":"uint128"},{"type":"uint256"},{"type":"uint256"},{"type":"uint128"},{"type":"uint128"}],"stateMutability":"view","type":"function"}]
POOL_ABI = [{"name":"slot0","inputs":[],"outputs":[{"type":"uint160"},{"type":"int24"},{"type":"uint16"},{"type":"uint16"},{"type":"uint16"},{"type":"uint32"},{"type":"bool"}],"stateMutability":"view","type":"function"}]
FACTORY_ABI = [{"name":"getPool","inputs":[{"type":"address"},{"type":"address"},{"type":"uint24"}],"outputs":[{"type":"address"}],"stateMutability":"view","type":"function"}]

# ========= 数据库逻辑 =========

def query_db_stats():
    connection = None
    try:
        connection = pymysql.connect(
            host=os.getenv("DB_HOST"),
            port=int(os.getenv("DB_PORT", 3306)),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
            cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=5
        )
        with connection.cursor() as cursor:
            # 核心：使用 IFNULL 确保数据库层面返回 0 而不是 NULL
            sql = "SELECT IFNULL(SUM(usdt_amount), 0) as total_usdt FROM user"
            cursor.execute(sql)
            result = cursor.fetchone()
            return Decimal(result['total_usdt'])
    except Exception as e:
        print(f"DB Error: {e}")
        return Decimal(0) # 报错返回 0
    finally:
        if connection: connection.close()

# ========= 链上数学逻辑 =========

def sqrtPriceX96_to_decimal(v): return Decimal(v) / Decimal(2**96)
def tick_to_sqrtPrice(tick): return Decimal(1.0001) ** Decimal(tick / 2)
def get_amounts(liquidity, sqrtPrice, sqrtLower, sqrtUpper):
    liquidity = Decimal(liquidity)
    if sqrtPrice <= sqrtLower: return liquidity * (sqrtUpper - sqrtLower) / (sqrtLower * sqrtUpper), Decimal(0)
    elif sqrtPrice < sqrtUpper:
        return liquidity * (sqrtUpper - sqrtPrice) / (sqrtPrice * sqrtUpper), liquidity * (sqrtPrice - sqrtLower)
    else: return Decimal(0), liquidity * (sqrtUpper - sqrtLower)

# ========= 核心执行 =========

def run_report():
    report = "📊 *综合业务资产报表*\n\n"
    
    # 1. 数据库业务查询
    db_total = query_db_stats()
    report += "🗄 *业务系统统计*\n"
    report += f"  • 用户总余额: `{float(db_total):,.2f} USDT`\n\n"

    # 2. 通用余额查询
    token_raw = os.getenv("TOKEN_CHECK_LIST", "")
    if token_raw:
        report += "💰 *钱包代币余额*\n"
        for item in token_raw.split(","):
            try:
                parts = item.strip().split(":")
                w_addr, t_addr, label = parts[0], parts[1], parts[2]
                if t_addr.upper() == "BNB":
                    amt = Decimal(w3.eth.get_balance(w_addr)) / Decimal(10**18)
                    sym = "BNB"
                else:
                    c = w3.eth.contract(address=Web3.to_checksum_address(t_addr), abi=ERC20_ABI)
                    amt = Decimal(c.functions.balanceOf(w_addr).call()) / Decimal(10**c.functions.decimals().call())
                    sym = c.functions.symbol().call()
                report += f"  • {label}: `{amt:.4f} {sym}`\n"
            except: continue
        report += "\n"

    # 3. Pancake LP 查询
    nft_raw = os.getenv("NFT_CONFIGS", "")
    if nft_raw:
        report += "🥞 *Pancake LP 持仓*\n"
        pm = w3.eth.contract(address=POSITION_MANAGER, abi=PM_ABI)
        factory = w3.eth.contract(address=FACTORY, abi=FACTORY_ABI)
        for item in nft_raw.split(","):
            try:
                nft_id, label = item.strip().split(":")
                pos = pm.functions.positions(int(nft_id)).call()
                t0, t1, fee, tl, tu, liq = pos[2], pos[3], pos[4], pos[5], pos[6], pos[7]
                
                c0, c1 = w3.eth.contract(address=t0, abi=ERC20_ABI), w3.eth.contract(address=t1, abi=ERC20_ABI)
                pool_addr = factory.functions.getPool(t0, t1, fee).call()
                sqrtP = sqrtPriceX96_to_decimal(w3.eth.contract(address=pool_addr, abi=POOL_ABI).functions.slot0().call()[0])
                amt0, amt1 = get_amounts(liq, sqrtP, tick_to_sqrtPrice(tl), tick_to_sqrtPrice(tu))
                
                report += f"  • {label} (ID: `{nft_id}`)\n"
                report += f"    `{amt0/Decimal(10**c0.functions.decimals().call()):.2f} {c0.functions.symbol().call()}` / `{amt1/Decimal(10**c1.functions.decimals().call()):.2f} {c1.functions.symbol().call()}`\n"
            except: continue

    return report

def send_tg(msg):
    if not TG_BOT_TOKEN: return
    try:
        requests.post(f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage", 
                      json={"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=10)
    except: pass

if __name__ == "__main__":
    final_msg = run_report()
    print(final_msg)
    send_tg(final_msg)
