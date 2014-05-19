# -*- coding: utf-8 -*-
'''
    drape的db模块
    封装了部分数据库底层的操作
'''
import mysql.connector

from .. import debug

class Db(object):
    ''' db对象 '''
    def __init__(self, connect_args):
        self._conn = mysql.connector.connect(**connect_args)

        self.log_sql = False
        self.table_prefix = ''

    def query(self, sql, params=None, fetchone=False, bydict=True):
        '''
            执行一次数据库查询
            sql: 查询语句
            params: 查询参数, 默认是None
            fetchone: 是否只获取一行数据, 默认是False
            bydict: 是否以字典形式返回查询结果, 默认是True
        '''
        cursor = self._conn.cursor()
        try:
            cursor.execute(sql, params)
        finally:
            if self.log_sql:
                logger = debug.get_logger()
                logger.debug(sql)

        if bydict:
            column_names = cursor.column_names
            if fetchone:
                return _make_dict(column_names, cursor.fetchone())
            else:
                return [_make_dict(column_names, row) for row in cursor]
        else:
            if fetchone:
                return cursor.fetchone()
            else:
                return list(cursor)

    def execute(self, sql, params=None):
        '''
            执行一条sql语句
        '''
        cursor = self._conn.cursor()
        try:
            rowcount = cursor.execute(sql, params)
        finally:
            if self.log_sql:
                logger = debug.get_logger()
                logger.debug(sql)

        return {
            'last_insert_id': cursor.lastrowid,
            'row_count': rowcount
        }

    def transaction(self):
        return Transaction(self)

class Transaction(object):
    def __init__(self, db_obj):
        self.__db_obj = db_obj

    def __enter__(self):
        self.__db_obj._conn.start_transaction()
        return self

    def __exit__(self, errtype, errvalue, errtrace):
        if errvalue:
            self.__db_obj._conn.rollback()
        else:
            self.__db_obj._conn.commit()

def _make_dict(column_names, row):
    ''' 将查询结果按照列名组装成字典 '''
    if row is None:
        return None

    result_dict = {}
    for i, column in enumerate(column_names):
        result_dict[column] = row[i]
    return result_dict
