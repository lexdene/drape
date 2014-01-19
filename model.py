# -*- coding: utf-8 -*-

import db

from . import util


class LinkedModel(object):
    __cache = {}

    def __init__(self, table_name):
        self.__table_name = table_name
        self.__db = db.Db.singleton()

        # clear link data
        self.__clear_link_data()

    def alias(self, alias):
        ''' 给主表起个别名, 这将影响到select后的字段名称 '''
        self.__alias = alias
        return self

    def where(self, *args, **kwargs):
        ''' where条件 '''
        self.__where_list.extend(args)
        self.__where_list.append(kwargs)
        return self

    ASC = 'A'
    DESC = 'D'

    def order(self, field, sequence=ASC):
        '''
            排序条件
            field: 字段名
            sequence: 排序顺序, DESC/ASC, 默认ASC
        '''
        self.__order_list.append((field, sequence))
        return self

    def limit(self, length):
        ''' limit参数 '''
        assert util.isInt(length)
        self.__limit = length
        return self

    LEFT = 'left'
    RIGHT = 'right'

    def join(self, table_name, on=None, alias=None, join_type=LEFT):
        '''
            连接表
            table_name:  表名
            on:          连接条件
            alias:       别名, None表示不加别名, 默认为None
            join_type:   连接类型, left/right, 默认为left
        '''
        if alias is None:
            alias = table_name

        self.__join_list.append({
            'table_name': table_name,
            'on': on,
            'alias': alias,
            'join_type': join_type
        })
        return self

    def group(self, group):
        ''' group by '''
        self.__group_list.append(group)
        return self

    SQL_CALC_FOUND_ROWS = 'SQL_CALC_FOUND_ROWS'
    REFLECT_ALL = 'a'
    REFLECT_NONE = 'n'
    REFLECT_IF_UNDEFINE_FIELDS = 'i'
    REFLECT_ONLY_IN_LIST = 'l'

    def select(self, fields=None, sql_options=None, query_options=None,
               field_reflect_type=None, reflect_fields=None):
        '''
            构造select语句并执行
            fields:              返回的字段, 默认为空
            sql_options:         select的选项, 默认为空
            query_options:       query的选项, 字典形式
                fetchone:        只获取一行数据, 默认为False
                bydict:          以字典形式返回查询结果, 默认为True
            field_reflect_type:  自动反射字段的方式
                REFLECT_ALL:     反射全部字段
                REFLECT_NONE:    不反射任何字段
                REFLECT_IF_UNDEFINE_FIELDS:
                                 如果没有指定fields, 则反射全部字段,
                                 否则不反射任何字段
                REFLECT_ONLY_IN_LIST:
                                 只反射reflect_fields参数指定的字段
                默认为REFLECT_IF_UNDEFINE_FIELDS
        '''
        return self

    def find(self):
        result = self.limit(1).select()
        if len(result) < 1:
            return None
        else:
            return result[0]

    def count(self, count_field=None):
        '''
            获取符合条件的记录的数目
            count_field:  计数的列名, 默认为主表的id
        '''
        if count_field:
            field = 'count(%s)' % count_field
        else:
            table_alias_name = self.__table_name
            if self.__alias:
                table_alias_name = self.__alias

            field = 'count(`%s`.`%s`)' % (
                table_alias_name,
                'id'
            )

        result = self.select(
            fields=[field],
            query_options={
                'fetchone': True,
                'bydict': False
            }
        )
        return result[0]

    def found_rows(self):
        result = self.__db.query(
            'select FOUND_ROWS()',
            fetchone=True,
            bydict=False
        )

        return result[0]

    def select_and_count(self):
        ''' 同时获取select结果与匹配条件的结果数目 '''
        result = self.select(options=(SQL_CALC_FOUND_ROWS,))
        count = self.found_rows()
        return result, count

    def insert(self, *args, **kwargs):
        ''' 执行insert操作 '''
        return result['last_insert_id']

    def update(self, *args, **kwargs):
        ''' 执行update操作 '''
        return result['row_count']

    def __clear_link_data():
        self.__alias = None
        self.__where_list = list()
        self.__order_list = list()
        self.__join_list = list()
        self.__group_list = list()
