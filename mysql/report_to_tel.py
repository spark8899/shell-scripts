#!/root/report/venv/bin/python3
# pip3 install PyMySQL prettytable python-dotenv requests
# .env # file
"""
MYSQL_HOST=127.0.0.1
MYSQL_USER=root
MYSQL_PASS=root123
MYSQL_DB=data
TEL_BOT_TOKEN=xxx:xxxx
TEL_CHAT_ID=-xxxx
"""

import pymysql, os, requests, decimal

from pathlib import Path
from dotenv import load_dotenv
from prettytable import PrettyTable
from datetime import date

exec_directory = Path(__file__).resolve().parent
os.chdir(exec_directory)
load_dotenv()

MYSQL_HOST = os.getenv('MYSQL_HOST')
MYSQL_USER = os.getenv('MYSQL_USER')
MYSQL_PASS = os.getenv('MYSQL_PASS')
MYSQL_DB = os.getenv('MYSQL_DB')
TEL_BOT_TOKEN = os.getenv('TEL_BOT_TOKEN')
TEL_CHAT_ID = os.getenv('TEL_CHAT_ID')

today_str = date.today().strftime("%Y-%m-%d")
plan_query_user_info = f"""
select '人员' as name, num from user where create_time >= '{today_str}' and status>0
union all
select '课程' as course, num from course where create_time >= '{today_str}' and status>0
"""

def send_telegram_message(bot_token, chat_id, message):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": f"<pre>{message}</pre>",
        "parse_mode": "HTML"
    }
    response = requests.post(url, data=payload)
    if response.status_code == 200:
        print("send access！")
    else:
        print("send faild:", response.text)

def get_bsc_token_amount_raw(token_address: str, wallet_address: str) -> int:
    BSC_RPC="https://bsc-rpc.publicnode.com"
    token_address = token_address.strip()
    wallet_address = wallet_address.strip()
    wallet = wallet_address.lower().replace("0x", "")
    wallet = wallet.zfill(64)
    data = "0x70a08231" + wallet
    headers = {'Content-type': 'application/json'}
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "eth_call",
        "params": [
            {
                "to": token_address,
                "data": data
            },
            "latest"
        ]
    }
    resp = requests.post(BSC_RPC, headers=headers, json=payload, timeout=10)
    result = resp.json().get("result")

    if not result or result == "0x":
        return 0

    return int(result, 16)

def mysql_query(plan):
    db = pymysql.connect(host=MYSQL_HOST, user=MYSQL_USER, password=MYSQL_PASS, database=MYSQL_DB)
    cursor = db.cursor()
    cursor.execute(plan)
    data = cursor.fetchall()
    db.close()
    return data

def main():
    data_res = mysql_query(plan_query_user_info)
    headers = ['名称', '数量']
    table = PrettyTable(headers)
    for i, col in enumerate(headers):
        table.align[col] = "r"
    table.align[headers[0]] = "l"

    for row in data_res:
        formatted_row = []
        for value in row:
            if isinstance(value, (int, float, decimal.Decimal)):
                formatted_row.append(f"{value:,.2f}")
            else:
                formatted_row.append(str(value))
        table.add_row(formatted_row)

    token = "0x55d398326f99059fF775485246999027B3197955" # usdt
    wallet = "0xxxxxxx"
    raw = get_bsc_token_amount_raw(token, wallet)
    amount = raw / ( 10 ** 18)
    table.add_row(("余额", f"{amount:,.2f}"))
    table_str = table.get_string()

    print(table_str)
    send_telegram_message(TEL_BOT_TOKEN, TEL_CHAT_ID, table_str)

if __name__ == '__main__':
    main()
