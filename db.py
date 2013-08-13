# -*- coding: utf-8 -*-
'''
    drape的db模块
    封闭了部分数据库底层的操作
'''
from . import config, debug


class Db(object):
    ''' db对象 '''
    def __init__(self):
        dbconfig = config.get_value('db')
        self.__config = dbconfig
        if dbconfig['driver'] == 'mysql':
            import mysql.connector
            self.__driver = mysql.connector

            self.__conn = self.__driver.connect(
                host=dbconfig['host'],
                port=int(dbconfig['port']),
                user=dbconfig['user'],
                password=dbconfig['password'],
                database=dbconfig['dbname'],
                charset=dbconfig['charset'],
            )
        else:
            raise ValueError('no such driver: %s' % dbconfig['driver'])

    @classmethod
    def singleton(cls):
        ''' 获取单例 '''
        if not hasattr(cls, '_instance'):
            cls._instance = cls()
        return cls._instance

    def table_prefix(self):
        ''' 从配置中获取数据表前缀 '''
        return self.__config['tablePrefix']

    def query(self, sql, params=None, fetchone=False, bydict=True):
        '''
            执行一次数据库查询
            sql: 查询语句
            params: 查询参数, 默认是None
            fetchone: 是否只获取一行数据, 默认是False
            bydict: 是否以字典形式返回查询结果, 默认是True
        '''
        def make_dict(column_names, row):
            ''' 将查询结果按照列名组装成字典 '''
            result_dict = {}
            for i, column in enumerate(column_names):
                result_dict[column] = row[i]
            return result_dict

        cursor = self.__conn.cursor()
        try:
            cursor.execute(sql, params)
        finally:
            if self.__config['log_sql']:
                debug.sql(sql)

        if bydict:
            column_names = cursor.column_names
            if fetchone:
                return make_dict(column_names, cursor.fetchone())
            else:
                return [make_dict(column_names, row) for row in cursor]
        else:
            if fetchone:
                return cursor.fetchone()
            else:
                return list(cursor)

    def execute(self, sql, params=None):
        '''
            执行一条sql语句
        '''
        cursor = self.__conn.cursor()
        try:
            rowcount = cursor.execute(sql, params)
        finally:
            if self.__config['log_sql']:
                debug.sql(sql)

        return {
            'last_insert_id': cursor.lastrowid,
            'row_count': rowcount
        }
