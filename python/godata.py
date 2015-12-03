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
import chardet
import sys
import json
import urllib
from collections import OrderedDict
reload(sys)
sys.setdefaultencoding("utf-8")

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
    def url_md5(self,host,url,post_data,content_type,req_type):     #对url和参数进行md5运算并判断该url是否已经存在数据库中了，如果存在返回false，不存在返回md5
        strParam = ''
        newurltag = 0
        newurl = ''
        newcontent = ''
        if req_type == 'get':
            url = urllib.unquote(url)
            tmp = url.split('?')
            listParam = tmp[1].split('&')
            listParam.sort()
            for param in listParam:
                keyvalue = param.split('=')
                strParam += keyvalue[0]
                try:
                    jsondata = json.loads(keyvalue[1])
                    jsonlist = []
                    jsondict = {}
                    for i in jsondata:
                        jsondict[str(i)] = str(jsondata[i]) + '*'
                        jsonlist.append(i)
                    keyvalue[1] = jsondict
                    listParam[listParam.index(param)] = str(keyvalue[0])+'='+str(keyvalue[1])
                    jsonlist.sort()
                    for key in jsonlist:
                        strParam += key
                    newurltag = 1
                except Exception as err:
                    pass
            if newurltag:
                newurl = tmp[0]+'?'
                for i in listParam:
                    newurl = newurl+str(i)+'&'
                newurl = newurl[0:-1]
            strUrl = tmp[0]+strParam
        if req_type == 'post':
            if content_type == 'multipart/form-data':
                param_re = re.compile('name="(.*?)"')
                listParam = param_re.findall(post_data)
                listParam.sort()
                for param in listParam:
                    strParam += param
            else:
                listParam = urllib.unquote(post_data).split('&')
                listParam.sort()
                newcontenttag = 0
                for param in listParam:
                    keyvalue = param.split('=')
                    if len(keyvalue) == 1:
                        try:
                            jsondata = json.loads(keyvalue[0])
                            jsondict = {}
                            for i in jsondata:
                                jsondict[str(i)] = str(jsondata[i]) + '*'
                                strParam += str(i)
                            newcontent = jsondict
                        except Exception as err:
                            pass
                    else:
                        try:
                            jsondata = json.loads(keyvalue[1])
                            jsonlist = []
                            jsondict = {}
                            for i in jsondata:
                                jsondict[str(i)] = str(jsondata[i]) + '*'
                                jsonlist.append(i)
                            keyvalue[1] = jsondict
                            listParam[listParam.index(param)] = str(keyvalue[0])+'='+str(keyvalue[1])
                            for key in jsonlist:
                                strParam += key
                            newcontenttag = 1
                        except Exception as err:
                            strParam += keyvalue[0]
                            pass
                if newcontenttag:
                    for i in listParam:
                        newcontent = newcontent + str(i)+'&'
                    newcontent = newcontent[0:-1]
            strUrl = url+strParam
        m1 = md5.new()
        m1.update(strUrl)   
        strMd5 = m1.hexdigest()
        try:
            selectSql = "select id from httpRequest where host = '%s' and urlmd5 = '%s'" % (host, strMd5)
            data =  cur.execute(selectSql)
            conn.commit()
            if data == 0:
                return newurl,newcontent,strMd5
            else:
                return '','',''
        except Exception as err:
            print err
            print "md5查询出错"

    def handle_request(self, msg):
        flag = self.findword(msg)
        insert_flag = 0
        if flag == 1:
            str = msg.request.get_query()
            headers = msg.request.headers
            cookies = headers.get('Cookie')
            if cookies:
                cookies = cookies[0]
            else:
                cookies = ''
            referer = headers.get('Referer')
            if referer != None:
                referer = referer[0]
            else:
                referer = ''
            host = headers.get('Host')
            if host:
                host = host[0]
            else:
                host = ''
            content = msg.request.content
            url = msg.request.url
            content_type = headers.get('Content-Type')
            if content_type:
                ct_re = re.compile('multipart/form-data; boundary=')
                content_type = content_type[0]
                tmp = ct_re.findall(content_type)
                if tmp:
                    content_type = 'multipart/form-data'
            else:
                content_type = ''
            strMd5 = ''
           # print 'host: '+host
           # print 'url: '+url
           # print 'content: '+content
           # print 'cookie: '+cookies
            if content == '':
                req_type = 'get'
                if len(url.split('?')) != 1: #如果get型url请求没有传递参数直接过滤掉不写入数据库 
                    (newurl,newcontent,strMd5) = self.url_md5(host,url,'',content_type,req_type)
                    if strMd5:
                        insert_flag = 1
                    if newurl:
                        url = newurl
            else:
                r = chardet.detect(content)
                if r['encoding']:
                    req_type= 'post'
                    (newurl,newcontent,strMd5) = self.url_md5(host,url,content,content_type,req_type)
                    if strMd5:
                        insert_flag = 1
                    if newcontent:
                        content = newcontent
                else:
                    print 'content type: null'
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
if __name__ == '__main__':
    if len(sys.argv) == 2:
        fp = open('test.txt')
        for i in fp.readlines():
            data = i.split(' ')
            if data[0]=='get':
                m.url_md5('xx',data[1],'','','get')
            if data[0]=='post':
                m.url_md5('xx',data[1],data[2],'','post')
    else:
        m.run()
    cur.close()
    conn.close()
