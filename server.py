# -*- coding: utf-8 -*-
# @Time    : 2022/8/21 下午7:57
# @Author  : wanzhaofeng
# @File    : server_main.py

from flask import Flask, jsonify, request
from service_conf import *
import pymysql
import json

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False


def create_mysql_conn():
    # pymysql连接rebecca数据库
    conn = pymysql.connect(host=mysql_params['host'],
                           port=mysql_params['port'],
                           user=mysql_params['user'],
                           passwd=mysql_params['passwd'],
                           db=mysql_params['db'],
                           charset=mysql_params['charset'])

    return conn


@app.route("/select_data")
def select():
    conn = create_mysql_conn()
    # 创建一个游标
    cursor = conn.cursor()
    query_sql = "select * from student;"
    n = cursor.execute(query_sql)
    ls = ['Sno', 'Sname', 'Sex', 'Sage', 'Sdept']
    result_dic = {'count': n, 'table_name': 'student'}
    ls_2 = []
    for row in cursor:
        temp = {}
        for i in range(len(row)):
            temp[ls[i]] = row[i]
        ls_2.append(temp)
    result_dic['info'] = ls_2
    cursor.close()
    return json.dumps(result_dic)


@app.route("/insert_data", methods=["POST"])
def insert():
    conn = create_mysql_conn()
    # 创建一个游标
    cursor = conn.cursor()
    # 这个info_list = request.form.get("info")通过url
    # 下面这个通过body
    info_list = request.json.get("info")
    for info in info_list:
        sno = info['Sno']
        sname = info['Sname']
        sex = info['Sex']
        sage = info['Sage']
        sdept = info['Sdept']
        query_sql = "insert into student(Sno, Sname, Sex, Sage, Sdept) values({}, {}, {}, {}, {});".format(sno,
                                                                                                           repr(sname),
                                                                                                           repr(sex),
                                                                                                           sage,
                                                                                                           repr(sdept))
        cursor.execute(query_sql)
    cursor.close()
    conn.commit()

    ret_message = {"code": 0, "status": "successful"}
    return ret_message


@app.route("/update_date", methods=['PATCH'])
def update():
    conn = create_mysql_conn()
    cursor = conn.cursor()
    info_list = request.json.get("info")
    for info in info_list:
        sname = info['Sname']
        if sname == '李勇':
            query_sql = "update student set sage=20 where sname='{}';".format(sname)
            print(query_sql)
            cursor.execute(query_sql)
    # 修改后需要commit
    cursor.close()
    conn.commit()
    ret_message = {"code": 0, "status": "successful"}
    return ret_message


@app.route("/delete_data", methods=['DELETE'])
def delete():
    conn = create_mysql_conn()
    cursor = conn.cursor()
    info_list = request.json.get("info")
    for info in info_list:
        sno = info['Sno']
        query_sql = "delete from student where Sno={};".format(sno)
        cursor.execute(query_sql)
    # 删除后需要commit
    cursor.close()
    conn.commit()
    ret_message = {"code": 0, "status": "successful"}
    return ret_message


if __name__ == "__main__":
    app.run()
