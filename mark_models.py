# -*- coding: utf-8 -*-
# @Time    : 2022/8/18 下午5:50
# @Author  : wanzhaofeng
# @File    : mark_models.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, INT, BIGINT, VARCHAR, JSON, FLOAT, DATETIME, SMALLINT, TEXT, TIMESTAMP, sql
# from geoalchemy2 import Geometry, func
from datetime import datetime
from sqlalchemy import func
from sqlalchemy.types import UserDefinedType
from service_conf import *

SQLALCHEMY_DATABASE_URI = 'mysql+mysqldb://%s:%s@%s:%s/%s?charset=utf8' % (
    mysql_params['user'],
    mysql_params['passwd'],
    mysql_params['host'],
    mysql_params['port'],
    mysql_params['db']
)

# app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
# db = SQLAlchemy(app)

engine = create_engine(SQLALCHEMY_DATABASE_URI, echo=False, pool_pre_ping=True, pool_size=10, pool_recycle=3600)
Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
my_session = scoped_session(Session)

Base = declarative_base()
Base.metadata.bind = engine

class Geometry(UserDefinedType):
    def get_col_spec(self):
        return 'GEOMETRY'

    def bind_expression(self, bindvalue):
        return func.ST_GeomFromText(bindvalue, type_=self)

    def column_expression(self, col):
        return func.ST_AsText(col, type_=self)

class Project(Base):
    __tablename__ = 'mark_project'
    id = Column(BIGINT, primary_key=True, autoincrement=True)
    name = Column(VARCHAR(64), nullable=False, server_default='')
    description = Column(VARCHAR(256), nullable=False, server_default='')
    query_count = Column(INT, nullable=False, server_default='0')
    doc_count = Column(INT, nullable=False, server_default='0')
    labeled_query_count = Column(INT, nullable=False, server_default='0')
    labeled_doc_count = Column(INT, nullable=False, server_default='0')
    authority = Column(JSON, nullable=False)


class Task(Base):
    __tablename__ = 'mark_task'
    id = Column(BIGINT, primary_key=True, autoincrement=True)
    project_id = Column(BIGINT, nullable=False, server_default='0')
    committer = Column(VARCHAR(128), nullable=False, server_default='')
    create_time = Column(DATETIME, nullable=False, server_default=func.now())
    update_time = Column(DATETIME, nullable=False, server_default='1970-01-01 00:00:00', onupdate=func.now())
    use_time = Column(INT, nullable=False, server_default='0')
    mark_status = Column(SMALLINT, nullable=False, server_default='0')
    mark_checked = Column(SMALLINT, nullable=False, server_default='0')
    query_category = Column(VARCHAR(128), nullable=False, server_default='')
    query_version = Column(VARCHAR(128), nullable=False, server_default='')
    doc_category = Column(VARCHAR(128), nullable=False, server_default='')
    doc_version = Column(VARCHAR(128), nullable=False, server_default='')
    query_link_id = Column(VARCHAR(128), nullable=False, server_default='')
    query_link_offset = Column(FLOAT, nullable=False, server_default='0')
    point = Column(Geometry, nullable=False)
    recall_info = Column(JSON, nullable=False)
    doc_count = Column(INT, nullable=False, server_default='0')


Base.metadata.create_all()
