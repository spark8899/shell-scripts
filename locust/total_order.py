import pymysql, sys, time

host, user, password, database = "127.0.0.1", "root", "root1234", "order"

def mysql_query(plan):
    db = pymysql.connect(host=host, user=user, password=password, database=database)
    cursor = db.cursor()
    cursor.execute(plan)
    data = cursor.fetchall()
    db.close()
    return data

def query_order(mtime, n):
    table_list = ["00", "01", "02", "03", "04", "05", "06", "07"]
    timeArray = time.strptime(mtime, "%Y-%m-%d %H:%M:%S")
    timestamp = time.mktime(timeArray)
    t_list = [mtime]
    sumn = 0
    for i in range(1, n + 1):
        timeLocal = time.localtime(timestamp + i)
        t_list.append(time.strftime("%Y-%m-%d %H:%M:%S", timeLocal))
    print("query time:", ", ".join(t_list))
    for ts in t_list:
        summ = 0
        for tb in table_list:
            order = mysql_query("select count(*) as order_%s from order_%s where mtime BETWEEN '%s' AND '%s.999999'" % (tb, tb, ts, ts))[0][0]
            #print("%s order_%s: %s" % (ts, tb, order))
            summ = summ + order
        print("%s order_sum: %s" % (ts, summ))
        sumn = sumn + summ
    print("all order_sum:", sumn)

def main():
    # mtime = "2012-02-10 09:14:21"
    if len(sys.argv) < 2:
        print("please input ctime and stepping")
        sys.exit(110)
    mtime = sys.argv[1]
    n = int(sys.argv[2])
    query_order(mtime, n)

if __name__ == '__main__':
    main()
