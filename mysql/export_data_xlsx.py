#!/bin/env python3
# pip3 install PyMySQL pandas openpyxl

import pymysql
from sqlalchemy import create_engine
import pandas as pd

host="localhost"
user="user"
password="123456"
database="admin_user"

plan_user = "select id,email,mobile,create_time,update_time from user where mobile > 0"

def deal_str(data):
    data = str(data) + '\t'
    return data

def query_user():
    data_user = mysql_exec(plan_user)
    print("id,email,mobile,create_time,update_time")
    for user in data_user:
        print("%s,%s,%.13f,%s,%s" % (user[0],user[1],user[2],user[3],user[4]))

def query_to_xsl():
    engine = create_engine("mysql+pymysql://%s:%s@%s/%s" % (user, password, host, database))
    df = pd.read_sql(sql=plan_user, con=engine)
    df['id'] = df['id'].map(deal_str)
    df.to_excel('user.xlsx', sheet_name='data', index=False, float_format="%.13f")

def mysql_exec(plan):
    db = pymysql.connect(host=host, user=user, password=password, database=database)
    cursor = db.cursor()
    cursor.execute(plan)
    data = cursor.fetchall()
    db.close()
    return data

def main():
    #query_user()
    query_to_xsl()

if __name__ == '__main__':
    main()
