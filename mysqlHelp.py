import MySQLdb

def connect():
    try:
        conn=MySQLdb.connect(host='localhost',user='root',passwd='root',db='mitmproxy',port=3306)
        return conn
    except MySQLdb.Error,e:
        print "Mysql Error %d: %s" % (e.args[0], e.args[1])
