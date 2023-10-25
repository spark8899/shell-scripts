#!/bin/env python3
# pip3 install PyMySQL prettytable

import pymysql, sys
import prettytable as pt

host="127.0.0.1"
user="user"
password="abcd1234"
database="admin_user"

plan_query_user_info = "select id,email,mobile,status,create_time,update_time from user where id in"

def query_user_info(id_list):
    query_plan = "%s (%s)" % (plan_query_user_info, id_list)
    #print(query_plan)
    query_res = mysql_query(query_plan)
    return query_res

def mysql_query(plan):
    db = pymysql.connect(host=host, user=user, password=password, database=database)
    cursor = db.cursor()
    cursor.execute(plan)
    data = cursor.fetchall()
    db.close()
    return data

def main():
    if len(sys.argv) < 2:
        print("please input user_info [\"id list\"]")
        sys.exit(110)
    user_id_list = "\"%s\"" % '\",\"'.join(sys.argv[1:])
    user_info_res = query_user_info(user_id_list)
    table = pt.PrettyTable(['id','email','mobile','status','create_time','update_time'])
    for i in user_info_res:
        table.add_row(i)
    print(table)

if __name__ == '__main__':
    main()
