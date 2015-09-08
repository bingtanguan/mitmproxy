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
import md5

re_rule = '(css|js|swf|jpg|gif|jpeg|bmp|png)$'
re_cmp = re.compile(re_rule,re.I)
conn = mysqlHelp.connect()
cur = conn.cursor()


def create_insert_sql(target_table, insert_data):
    '''生成 insert sql
        example:
        create_insert_sql('`users`', {
                    'name': 'moca',
                    'password': '123456'
                })

    得到 INSERT INTO `users` (password, name) VALUES (%s, %s)

    '''

    # 转str类型
    for x in insert_data:
        insert_data[x] = str(insert_data[x])

    sql = 'INSERT INTO {target_table} {columns} VALUES {values}' .format(
        target_table=target_table,
        columns=(tuple(insert_data.keys())),
        values=(('%s',) * len(insert_data))
    )
    final_sql = sql.replace("'", '')
    return final_sql


class StickyMaster(controller.Master):
    def __init__(self, server):
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
        print url
        if flag:
#            print 'jingtai:'+url
            return 0
        else:
#            print 'dongtai:'+url
            return 1
    def url_md5(self,host,url,post_data,req_type):     #对url和参数进行md5运算并判断该url是否已经存在数据库中了，如果存在返回false，不存在返回md5
        strParam = ''
        if req_type == 'get':
            tmp = url.split('?')
            listParam = tmp[1].split('&')
            listParam.sort()
            for param in listParam:
                strParam += param.split('=')[0]
            strUrl = tmp[0]+strParam
        if req_type == 'post':
            listParam = post_data.split('&')
            listParam.sort()
            for param in listParam:
                strParam += param.split('=')[0]
            strUrl = url+strParam
        print strParam
        m1 = md5.new()
        m1.update(strUrl)   
        strMd5 = m1.hexdigest()
        try:
            selectSql = "select id from httpRequest where host = '%s' and urlmd5 = '%s'" % (host, strMd5)
            data =  cur.execute(selectSql)
            if data == 0:
                return strMd5
            else:
                return False
        except Exception as err:
            print "md5查询出错"

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
                    print "cookie error: "+cookies
            else:
                cookies = ''
            referer = headers.get('Referer')
            if referer != None:
                referer = referer[0]
            else:
                referer == ''
            content = msg.request.content
            host = list(headers)[0][1]
            url = msg.request.url
            strMd5 = ''
            if content == '':
                req_type = 'get'
                if len(url.split('?')) != 1: #如果get型url请求没有传递参数直接过滤掉不写入数据库 
                    strMd5 = self.url_md5(host,url,'',req_type)
                    if strMd5:
                        insert_flag = 1
            else:
                req_type= 'post'
                strMd5 = self.url_md5(host,url,content,req_type)
                if strMd5:
                    insert_flag = 1
            if insert_flag:
                try:
                    some_submit_data= {
                        'type': req_type,
                        'host': host,
                        'url': url,
                        'cookie': cookies,
                        'postdata': content,
                        'referer': referer,
                        'sqlistatus':'not start',
                        'urlmd5':strMd5
                    }
                    sqlinsert=create_insert_sql('httpRequest',some_submit_data)
                    cur.execute(sqlinsert,tuple(some_submit_data.values()))
                    conn.commit()
                except Exception as err:
                    print err
        msg.reply()       
 
    def handle_response(self, msg):
        msg.reply()
 
config = proxy.ProxyConfig(
    port=8100,
    # use ~/.mitmproxy/mitmproxy-ca.pem as default CA file.
    cadir="~/.mitmproxy/"
)
server = ProxyServer(config)
m = StickyMaster(server)
m.run()
cur.close()
conn.close()
