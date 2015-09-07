#!/usr/bin/env python
#coding=utf-8
"""
author:rainau
time:2015-08-13 19:33
"""
from libmproxy import controller, proxy
from libmproxy.proxy.server import ProxyServer
import os
import pdb
import re
import mysqlHelp
import sys

re_rule = '(css|js|swf|jpg|gif|jpeg|bmp|png)$'
re_cmp = re.compile(re_rule,re.I)
conn = mysqlHelp.connect()
cur = conn.cursor()
class StickyMaster(controller.Master):
    def __init__(self, server, url_filter):
        self.url_filter = url_filter
        self.re_url_filter = re.compile(self.url_filter)
        controller.Master.__init__(self, server)
    def run(self):
        try:
            return controller.Master.run(self)
        except KeyboardInterrupt:
            self.shutdown()
 
    def findword(self,msg):
        querystring = msg.request.get_query()
        url = msg.request.url
        flag = re_cmp.search(url.split('?')[0])
#        print url
        if flag:
#            print 'jingtai:'+url
            return 0
        else:
#            print 'dongtai:'+url
            if url_filter == "":
                print 'xx'
                return 1
            else:
                if self.re_url_filter.search(url):
                    return 1
                else:
                    return 0
 
    def handle_request(self, msg):
        flag = self.findword(msg)
        insert_flag = 0
        if flag == 1:
            str = msg.request.get_query()
            headers = msg.request.headers
            cookies = headers.get('Cookie')
            if cookies:
                try:
                    cookies = cookies[0].replace("'","\'")
                except:
                    print cookies
            else:
                cookies = ''
            referer = headers.get('Referer')
            content = msg.request.content
            url = msg.request.url
            if content == '':
                req_type = 'get'
                if len(url.split('?')) != 1: #如果get型url请求没有传递参数直接过滤掉不写入数据库 
                    insert_flag = 1
            else:
                req_type= 'post'
                content = content.replace("'","\'")
                insert_flag = 1
            host = url.split('//')[1].split('/')[0]
            if insert_flag:
                try:
                    print "url:    "+ url
                    print "cookie:   "+cookies
                    print "content:   "+content
                    cur.execute('insert into httpRequest values (0,\'%s\',\'%s\',\'%s\',\'%s\',\'%s\')' % (req_type,host,url,cookies,content))
                    conn.commit()
                except Exception as err:
                    print err
            '''
            print 'query:\n'
            for eachp in str:
                print eachp[0] + '=' + eachp[1]+'&'
            print '\ncookie:'
            print cookies
            print '\n'
            print 'data:'
            print content
            print '\n'
            print 'url:'
            print url
            print '\n'
            print 'referer:'
            print referer
            print '------------------\n'
            '''
        msg.reply()       
 
    def handle_response(self, msg):
        msg.reply()
 
config = proxy.ProxyConfig(
    port=8105,
    # use ~/.mitmproxy/mitmproxy-ca.pem as default CA file.
    cadir="~/.mitmproxy/"
)
if __name__ == '__main__':
    server = ProxyServer(config)
    if sys.argv == 2:
        url_filter = sys.argv[1]
    else:
        url_filter = ""
    m = StickyMaster(server,url_filter)
    m.run()
    cur.close()
    conn.close()
