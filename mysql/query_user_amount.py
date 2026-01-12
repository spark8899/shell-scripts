#!/bin/env python3
# pip3 install PyMySQL prettytable python-dotenv
# .env # file
"""
MYSQL_HOST=127.0.0.1
MYSQL_USER=root
MYSQL_PASS=root123
MYSQL_DB=data
"""

import pymysql, os, sys

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

today_str = date.today().strftime("%Y-%m-%d")

plan_query_user_amount = f"""
select id, amount, update_time from user_account where update_time >= '{today_str}' and id in
"""

def query_user_amount(id_list):
    query_plan = "%s (%s)" % (plan_query_user_amount, id_list)
    query_res = mysql_query(query_plan)
    return query_res

def mysql_query(plan):
    db = pymysql.connect(host=MYSQL_HOST, user=MYSQL_USER, password=MYSQL_PASS, database=MYSQL_DB)
    cursor = db.cursor()
    cursor.execute(plan)
    data = cursor.fetchall()
    db.close()
    return data

def main():
    if len(sys.argv) < 2:
        print("please input user_id [\"id list\"]")
        sys.exit(110)
    id_list = "\"%s\"" % '\",\"'.join(sys.argv[1:])
    res = query_user_amount(id_list)
    table = PrettyTable(['id','amount','update_time'])
    for i in res:
        table.add_row(i)
    print(table)

if __name__ == '__main__':
    main()
