#coding=utf-8
import requests
import json
from time import sleep
import time
import mysqlHelp
"""
    author:rainau
    time:2015-9-7
"""
conn = mysqlHelp.connect()
cur = conn.cursor()


class SqlmapTask(object):

    def __init__(self,server):
        self.server = server
    def task_new(self):
        self.taskid = json.loads(requests.get(self.server + '/task/new').text)['taskid']
        return self.taskid

    def task_delete(self,taskid):
        status = json.loads(requests.get(self.server + 'task/taskid/delete'))['success']
        return status

    def task_option_set(self,taskid,option,value):
        headers = {'Content-Type': 'application/json'}
        taskOption = {
                      option:value
                     }
        data = json.loads(
                        requests.post(self.server + '/option/' + taskid + '/set', data = json.dumps(taskOption), headers = headers).text)
        

    def scan_start(self,taskid,target_url):
        headers = {'Content-Type': 'application/json'}
        payload = {'url': target_url}
        url = self.server + '/scan/' + taskid + '/start'
        t = json.loads(
            requests.post(url, data=json.dumps(payload), headers=headers).text)
        self.engineid = t['engineid']
        if len(str(self.engineid)) > 0 and t['success']:
            print 'Started scan id '+taskid
            updatestatus = 'update httpRequest set sqlistatus = "running" where taskid = "%s"' % taskid
            cur.execute(updatestatus)
            conn.commit()

    def scan_injectable(self):
        query = 'select taskid from httpRequest where sqlistatus = "running"'
        while True:
            cur.execute(query)
            conn.commit()
            rows = cur.fetchall()
            for row in rows:
                taskid =  row[0]
                if self.scan_status(taskid) == 'terminated':  #判断注入结束
                    updatestatus = 'update httpRequest set sqlistatus = "terminated" where taskid = "%s"' % taskid
                    cur.execute(updatestatus)
                    conn.commit()
                    if self.scan_data(taskid):  #存在注入
                        updateinject = 'update httpRequest set injectable= "true" where taskid = "%s"' % taskid
                        print "taskid:"+taskid+" 存在注入"
                    else:   #不存在注入
                        updateinject = 'update httpRequest set injectable= "false" where taskid = "%s"' % taskid
                        print "taskid:"+taskid+" 不存在注入"
                    cur.execute(updateinject)
                    conn.commit()
            sleep(15)
 

    def scan_status(self,taskid):
        status = json.loads(
                requests.get(self.server + '/scan/' + taskid + '/status').text)['status']
        return status

    def scan_stop(self,taskid):
        pass

    def scan_data(self,taskid):
        data = json.loads(
                requests.get(self.server + '/scan/' + taskid + '/data').text)['data']
        if len(data) > 0:  #存在注入
            return True
        else:
            return False

def run():
    test = SqlmapTask("http://192.168.0.50:8775")
    selectquery = 'select * from httpRequest where sqlistatus = "not start"'
    while True:
        cur.execute(selectquery)
        conn.commit()
        rows = cur.fetchall()
        for row in rows:
            req_type = row[1]
            url = row[3]
            cookie = row[4]
            postdata = row[5]
            urlmd5 = row[9]
            taskid = test.task_new()
            if len(taskid)>0:
                update = 'update httpRequest set taskid = "%s" where urlmd5 = "%s"' % (taskid,urlmd5)
                cur.execute(update)
                conn.commit()
                test.task_option_set(taskid,"cookie",cookie)
                if req_type == 'post':
                    try:
                        test.task_option_set(taskid,"data",postdata)
                        test.scan_start(taskid,url)
                    except Exception as err:
                        update = 'update httpRequest set sqlistatus= "start error" where urlmd5 = "%s"' % (urlmd5)
                        cur.execute(update)
                        conn.commit()
                        print "taskid: "+taskid+ " start error"
                else:
                    test.scan_start(taskid,url)
            else:
                    print 'create  job error'
        sleep(5)

   # test = SqlmapTask("http://192.168.0.58:8775")    
   # taskid = test.task_new()
   # if len(taskid) > 0:
   #     test.task_option_set(taskid,"cookie","ffdsafs")
   #     test.task_option_set(taskid,"agent","fdas")
   #     if test.scan_start(taskid,"http://www.cuit.edu.cn/ShowNews?id=1300"):
   #         print '存在注入---------'
   #     else:
   #         print '不存在注入-------'

   # else:
   #     print "create job error"
   # 

if __name__ == '__main__':
#    test = SqlmapTask("http://192.168.0.58:8775")    
#    taskid = test.task_new()
#    if len(taskid) > 0:
#        test.task_option_set(taskid,"cookie","ffdsafs")
#        test.task_option_set(taskid,"agent","fdas")
#        if test.scan_start(taskid,"http://www.cuit.edu.cn/ShowNews?id=1300"):
#            print '存在注入---------'
#        else:
#            print '不存在注入-------'
#
#    else:
#        print "create job error"
#
    run()
