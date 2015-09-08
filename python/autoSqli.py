#coding=utf-8
import requests
import json
from time import sleep
"""
    author:rainau
    time:2015-9-7
"""


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
            while True:
                sleep(10)
                if self.scan_status(taskid) == 'terminated':  #判断注入结束
                    if self.scan_data(taskid):
                        return True #存在注入
                    else:
                        return False #不存在注入
                    break
        return False

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


if __name__ == '__main__':
    test = SqlmapTask("http://192.168.0.58:8775")    
    taskid = test.task_new()
    if len(taskid) > 0:
        test.task_option_set(taskid,"cookie","ffdsafs")
        test.task_option_set(taskid,"user-agent","fdas")
        if test.scan_start(taskid,"http://www.cuit.edu.cn/ShowNews?id=1300"):
            print '存在注入---------'
        else:
            print '不存在注入-------'

    else:
        print "create job error"

