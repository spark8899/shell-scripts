#!/bin/env python3
# pip3 install PyMySQL pandas openpyxl requests

import requests, json, pymysql, sys
import pandas as pd

host="127.0.0.1"
user="user01"
password="pasdsdd"
database="user_sys"

plan_query_user_info = "select user_id,name,email,amount from user where email ="
summer = 0
ds = []

def query_user_info(email):
    global summer
    query_plan = "%s \"%s\"" % (plan_query_user_info, email_list)
    query_res = mysql_query(query_plan)[0]
    summer += int(query_res[3])
    ds.append({"name": query_res[1], "email": query_res[2], "amount": int(query_res[3])})
    return str(query_res[0])

def mysql_query(plan):
    db = pymysql.connect(host=host, user=user, password=password, database=database)
    cursor = db.cursor()
    cursor.execute(plan)
    data = cursor.fetchall()
    db.close()
    return data

def query_level(level, userId):
    global summer
    url = "http://localhost:19100/user/Invitee"
    headers = {'Content-type': 'application/json', 'userId': userId}
    req = requests.get(url, headers=headers, timeout=5).json()
    if req['code'] == "success":
        for data in req['data']:
            userID = data["userId"]
            if 'name' in data:
                name = data['name']
            else:
                name = 'NULL'
            email = data["email"]
            amount = data["amount"]
            summer += int(amount)
            ds.append({"name": name, "email": email, "amount": int(amount)})
            query_level(level + 1, userID)

def main():
    if len(sys.argv) < 2:
        print("please input email")
        sys.exit(110)
    email = "\"%s\"" % sys.argv[1]
    user_id = query_user_info(email)

    query_level(1, user_id)
    #print("total: ", summer)

    df = pd.DataFrame(ds)
    df.loc[len(df)] = ['合计：', '', df[['amount']].sum(axis=0)['amount']]
    pd.set_option('display.unicode.ambiguous_as_wide', True)
    pd.set_option('display.unicode.east_asian_width', True)
    pd.set_option('display.width', 180)
    print(df)
    df.to_excel("level.xlsx", sheet_name='data', index=False)

if __name__ == '__main__':
    main()
