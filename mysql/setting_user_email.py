#!/bin/env python3
# pip3 install PyMySQL

import pymysql, sys, os

host="127.0.0.1"
user="user"
password="abcd1234"
database="admin_user"

def load_address_list(user_list_path):
    with open(user_list_path, 'r') as f:
        user_list = []
        reader = f.readlines()
        for i in reader:
            user_list.append(i.strip().split(' ')[0])
    return user_list

def setting_user_email(email, user_list):
    query_plan = "update user set email=\"%s\",update_time='2022-03-03 03:03:04' where id in (%s)" % (email, user_list)
    #print(query_plan)
    mysql_exec(query_plan)

def mysql_exec(plan):
    conn = pymysql.connect(host=host, user=user, password=password, database=database)
    cursor = conn.cursor()
    try:
        cursor.execute(plan)
        conn.commit()
    except Exception as e:
        print("sql runing exception:",e)
        conn.rollback()
    cursor.close()
    conn.close()

def main():
    if len(sys.argv) != 2:
        print("please input user_email file.")
        sys.exit(110)
    file_path = sys.argv[1]
    if not os.path.isfile(file_path):
        print("file %s is not exists." % file_path)
        sys.exit(110)
    user_email_list = load_address_list(file_path)
    setting_user_email('test@mail.com', user_email_list)
    print()

if __name__ == '__main__':
    main()
