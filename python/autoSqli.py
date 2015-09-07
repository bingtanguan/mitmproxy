#coding=utf-8
import requests
import json
"""
    author:rainau
    time:2015-9-7
"""


class SqlmapTask(object):

    def __init__(self,server):
        self.taskid = ''
        self.server = server
    def task_new(self):
        self.taskid = json.loads(requests.get(self.server + '/task/new').text)['taskid']
        return self.taskid

    def task_delete(self,taskid):
        status = json.loads(requests.get(self.server + 'task/taskid/delete'))['success']
        return status

    def task_option_set(self):
        pass

    def scan_start(self,taskid,target_url):
        headers = {'Content-Type': 'application/json'}
        payload = {'url': target_url}
        url = self.server + '/scan/' + self.taskid + '/start'
        t = json.loads(
            requests.post(url, data=json.dumps(payload), headers=headers).text)
        self.engineid = t['engineid']
        if len(str(self.engineid)) > 0 and t['success']:
            print 'Started scan'
            return True
        return False

    def scan_status(self):
        pass

    def scan_stop(self):
        pass

    def scan_data(self):
        pass


if __name__ == '__main__':
    test = SqlmapTask("http://192.168.0.59:8775")    
    taskid = test.task_new()
    if len(taskid) > 0:
        if test.scan_start(taskid,"http://testphp.vulnweb.com/artists.php?artist=1"):
            print "start test" + taskid
        else:
            print "start error------"

    else:
        print "create job error"

