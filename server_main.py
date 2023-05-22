# -*- coding: utf-8 -*-
# @Time    : 2022/8/21 下午7:57
# @Author  : wanzhaofeng
# @File    : server_main.py


import flask
import flask_restless
from flask_restless import ProcessingException
from mark_models import *

app = flask.Flask(__name__)
URL_PREFIX = '/roadmatch-mark'


@app.teardown_appcontext
def shutdown_session(exception=None):
    my_session.remove()


# 检查字段
def check_field(data, field_dic):
    for key, value in field_dic.items():
        if data.has_key(key) and str(data[key]) != str(value):
            raise ProcessingException("the {0} is different from database".format(key), 406)


# 领取单个任务/提交标注信息
def pre_update_single_task(instance_id, data):
    if not instance_id:
        raise ProcessingException('instance_id can not be None', 406)
    if not data:
        raise ProcessingException('body can not be None', 406)
    check_info = my_session.query(Task).filter(Task.id == int(instance_id)).first()
    # print(check_info)
    # 提交标注信息
    if data.has_key('recall_info'):
        field_dic = {'query_category': check_info.query_category, 'query_version': check_info.query_version,
                     'doc_category': check_info.doc_category, 'doc_version': check_info.doc_version,
                     'query_link_id': check_info.query_link_id, 'query_link_offset': check_info.query_link_offset,
                     'committer': check_info.committer}
        check_field(data, field_dic)
        ret_doc_count = len(data['recall_info'])
        if ret_doc_count != int(check_info.doc_count):
            raise ProcessingException("the ret_doc_count is different from database", 406)
        mark_flag = True
        ret_recall_info = data['recall_info']
        check_recall_info = check_info.recall_info
        for i in range(len(ret_recall_info)):
            if ((str(ret_recall_info[i][0]) != str(check_recall_info[i][0]))
                    or (str(ret_recall_info[i][1]) != str(check_recall_info[i][1]))
                    or (str(ret_recall_info[i][2]) != str(check_recall_info[i][2]))
                    or (str(ret_recall_info[i][3]) != str(check_recall_info[i][3]))
                    or ret_recall_info[i][4] not in [0, 1, 2, 3, 4]):
                mark_flag = False
                break
        if not mark_flag:
            raise ProcessingException("some subtask are not marked", 406)
    # 领取单个任务
    else:
        if str(check_info.committer) != "" and str(check_info.mark_status) == "0":
            raise ProcessingException("the task was assigned to others people", 406)


# {"q": {"filters":[{"or":[{"name":"id","op":"==","val":2892},{"name":"id","op":"==","val":38628}]}, {"name":"project_id","op":"==","val":1}]}}
# 批量领取任务
def pre_update_many_task(search_params=None, data=None, **kw):
    if not search_params:
        raise ProcessingException('search_params can not be None', 406)
    if not data:
        raise ProcessingException('data can not be None', 406)
    if not search_params['filters'][0]['or']:
        raise ProcessingException('the task to be assigned is empty', 406)
    for task in search_params['filters'][0]['or']:
        task_database_info = my_session.query(Task).filter(Task.id == int(task['val'])).first()
        if str(task_database_info.committer) != "" and str(task_database_info.mark_status) == "0":
            raise ProcessingException("the task:{0} was assigned to others people".format(task['val']), 406)


def update_authority(data, authority_info_dic):
    authority_ways = ['create', 'delete', 'update', 'admin']
    if data['authority']['way'] == "add":
        for way in authority_ways:
            if data['authority'][way] and (not authority_info_dic[way].__contains__(data['authority'][way])):
                authority_info_dic[way].append(data['authority'][way])
    if data['authority']['way'] == "delete":
        for way in authority_ways:
            if data['authority'][way] and authority_info_dic[way].__contains__(data['authority'][way]):
                authority_info_dic[way].remove(data['authority'][way])


# 修改项目名称描述信息、权限
def pre_single_project(instance_id, data):
    if not instance_id:
        raise ProcessingException('instance_id can not be None', 406)
    if not data:
        raise ProcessingException('body can not be None', 406)
    if data.has_key('authority'):
        authority_info_dic = my_session.query(Project).filter(Project.id == int(instance_id)).first().authority
        update_authority(data, authority_info_dic)
        my_session.query(Project).filter(Project.id == int(instance_id)).update({"authority": authority_info_dic})
        my_session.flush()
        my_session.commit()

        raise ProcessingException("permission assigned successfully", 200)


def pre_get_many_project(search_params=None, **kw):
    select_project = my_session.query(Project).filter().all()
    for project in select_project:
        project_id = project.id
        query_count = my_session.query(func.count('*')).select_from(Task).filter(Task.project_id == project_id).scalar()
        labeled_query_count = my_session.query(func.count('*')).select_from(Task).filter(Task.project_id == project_id,
                                                                                         Task.mark_status == 1).scalar()
        doc_count = my_session.query(func.sum(Task.doc_count)).filter(Task.project_id == project_id).scalar()
        labeled_doc_count = my_session.query(func.sum(Task.doc_count)).filter(Task.project_id == project_id,
                                                                              Task.mark_status == 1).scalar()
        my_session.query(Project).filter(Project.id == project_id).update(
            {"query_count": query_count, "labeled_query_count": labeled_query_count, "doc_count": doc_count,
             "labeled_doc_count": labeled_doc_count})
    my_session.flush()
    my_session.commit()


manager = flask_restless.APIManager(app, session=my_session)
manager.create_api(Project,
                   methods=['GET', 'PATCH', 'POST'],
                   collection_name='mark_project',
                   url_prefix=URL_PREFIX,
                   results_per_page=20,
                   max_results_per_page=1000,
                   preprocessors=dict(PATCH_SINGLE=[pre_single_project],
                                      GET_MANY=[pre_get_many_project]),
                   validation_exceptions=[Exception])

manager.create_api(Task,
                   methods=['GET', 'PATCH'],
                   collection_name='mark_task',
                   url_prefix=URL_PREFIX,
                   results_per_page=5,
                   max_results_per_page=1000,
                   allow_patch_many=True,
                   preprocessors=dict(PATCH_SINGLE=[pre_update_single_task],
                                      PATCH_MANY=[pre_update_many_task]),
                   validation_exceptions=[Exception])

if __name__ == "__main__":
    app.config['JSON_AS_ASCII'] = True
    app.config['DEBUG'] = False
    app.run(host='0.0.0.0', port=8093)
