import os, random, time, datetime
from dotenv import load_dotenv
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware

# 1. 初始化
load_dotenv()
w3 = Web3(Web3.HTTPProvider(os.getenv("RPC_URL")))
w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

pk = os.getenv("PRIVATE_KEY")
acct = w3.eth.account.from_key(pk if pk.startswith("0x") else "0x" + pk)
wallet = acct.address
HISTORY_FILE = "history_addresses.txt"

# 2. 压缩版 ABI
ERC20_ABI = [{"constant":True,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"}, {"constant":False,"inputs":[{"name":"s","type":"address"},{"name":"v","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"type":"function"}, {"constant":True,"inputs":[{"name":"o","type":"address"},{"name":"s","type":"address"}],"name":"allowance","outputs":[{"name":"","type":"uint256"}],"type":"function"}]
AIRDROP_ABI = [{"inputs":[{"internalType":"address","name":"token","type":"address"},{"internalType":"address[]","name":"recipients","type":"address[]"},{"internalType":"uint256[]","name":"values","type":"uint256[]"}],"name":"disperseToken","outputs":[],"stateMutability":"nonpayable","type":"function"}]

def send_tx(txn_build):
    txn_build.update({'nonce': w3.eth.get_transaction_count(wallet)})
    signed = w3.eth.account.sign_transaction(txn_build, private_key=acct.key)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    w3.eth.wait_for_transaction_receipt(tx_hash)
    return tx_hash.hex()

def main():
    token = w3.eth.contract(address=Web3.to_checksum_address(os.getenv("TOKEN_ADDRESS")), abi=ERC20_ABI)
    airdrop = w3.eth.contract(address=Web3.to_checksum_address(os.getenv("AIRDROP_CONTRACT_ADDRESS")), abi=AIRDROP_ABI)
    decimals = token.functions.decimals().call()

    history_set = set()
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            # 读取所有行并去掉换行符
            history_set = {line.strip() for line in f if line.strip()}
    print(f"[0] 已加载历史空投记录，共 {len(history_set)} 个地址。")

    print("[1] 正在直接解析最新区块，提取 USDT 活跃接收者...")
    USDT_ADDR = "0x55d398326f99059fF775485246999027B3197955".lower()
    addrs_set = set()
    latest_block = w3.eth.block_number

    # 4. 抓取真实转账
    for i in range(20):
        block_num = latest_block - i
        print(f" -> 正在解析区块: {block_num} ...", end="\r")
        try:
            block = w3.eth.get_block(block_num, full_transactions=True)
            for tx in block.get("transactions", []):
                to_addr = tx.get("to")
                if to_addr and to_addr.lower() == USDT_ADDR:
                    inp_raw = tx.get("input", b"")
                    inp = Web3.to_hex(inp_raw).lower() if not isinstance(inp_raw, str) else inp_raw.lower()
                    if inp.startswith("0xa9059cbb") and len(inp) >= 138:
                        addr = Web3.to_checksum_address("0x" + inp[34:74])
                        # --- [新增] 只有当地址不在历史记录中，且不是黑洞地址时，才加入集合 ---
                        if addr not in history_set and addr != "0x0000000000000000000000000000000000000000":
                            addrs_set.add(addr)
        except Exception:
            pass
            
        if len(addrs_set) >= 50:
            print(f"\n[+] 目标达成，已在区块 {block_num} 抓满全新的活跃地址！")
            break

    print("") 
    addrs = list(addrs_set)
    if not addrs: 
        return print("[-] 未抓取到全新地址（或全部为已空投过的老地址），请稍后再试。")

    # 5. 计算所需金额与授权
    values = [int(round(random.uniform(0.5, 1.0), 4) * (10**decimals)) for _ in addrs]
    total_needed_wei = sum(values)
    total_token_human =  total_needed_wei/ (10**decimals)

    print(f"[2] 成功抓取 {len(addrs)} 个全新地址, 预计消耗 {total_token_human:.4f} Token")

    current_balance = token.functions.balanceOf(wallet).call()
    if current_balance < total_needed_wei:
        print(f"[-] 钱包 Token 余额不足！当前余额: {current_balance / (10**decimals):.4f}，但需要: {total_token_human:.4f}")
        return

    if token.functions.allowance(wallet, airdrop.address).call() < sum(values):
        print("[3] 正在向空投合约授权 (Approve)...")
        send_tx(token.functions.approve(airdrop.address, 2**256 - 1).build_transaction({'from': wallet}))

    # 6. 分批次执行打币并收集 Hash
    print("[4] 开始批量空投...")
    tx_hashes = []
    
    for i in range(0, len(addrs), 150):
        b_addrs, b_vals = addrs[i:i+150], values[i:i+150]
        tx_hash = send_tx(airdrop.functions.disperseToken(token.address, b_addrs, b_vals).build_transaction({'from': wallet}))
        print(f" -> 第 {i//150 + 1} 批次成功! TxHash: {tx_hash}")
        tx_hashes.append(tx_hash)
        time.sleep(1)

    # 7. 写入精简日志，并保存新的历史地址
    log_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{log_time}] 空投全新地址数: {len(addrs)}, 消耗Token: {total_token_human:.4f}, TxHashes: {', '.join(tx_hashes)}\n"
    
    with open("airdrop_record.log", "a", encoding="utf-8") as f:
        f.write(log_line)
        
    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        for a in addrs:
            f.write(a + "\n")
            
    print("[5] 全部完成！日志已追加，新地址已存入 history_addresses.txt 避免重复。")

if __name__ == "__main__":
    main()
