#!/bin/python3
# pip3 install PyMySQL jinja2
import os, json, pymysql, jinja2, time
from datetime import timezone, timedelta

db_host="127.0.0.1"
db_user="user001"
db_password="passwd002"
db_database="user"

template_path = "/root/tools/data_total/data.template"
save_path = "/opt/app/static/data_total/result.html"

plan_user_pay = "select email, amount, update_time as datatime from user where amount > 0 order by update_time desc"

def generate_html(total, body):
    with open(template_path) as file_:
        template = jinja2.Template(file_.read())
    with open(save_path, 'w+') as f:
        html_content = template.render(total=total, body=body)
        f.write(html_content)

def mysql_exec(plan):
    db = pymysql.connect(host=db_host, user=db_user, password=db_password, database=db_database)
    cursor = db.cursor()
    cursor.execute(plan)
    data = cursor.fetchall()
    db.close()
    return data

def main():
    res_user_pay = mysql_exec(plan_user_pay)
    pay_info = []
    total_amount = 0
    for i in res_user_pay:
        res = {"email": i[0], "amount": int(i[1]), "datetime": i[2].astimezone(timezone(timedelta(hours=+8))).strftime("%Y-%m-%d %H:%M:%S")}
        total_amount += int(i[1])
        pay_info.append(res)
    total = {"total_amount": total_amount, "total_user": len(pay_info)}

    # update html template
    generate_html(total, pay_info)
    print('### update html. ###')


if __name__ == '__main__':
    main()
