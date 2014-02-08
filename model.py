# -*- coding: utf-8 -*-

import db

from . import util


class FieldParam(object):
    ''' param as a field '''
    def __init__(self, name):
        self.name = name


class LinkedModel(object):
    __cache = {}

    def __init__(self, table_name):
        self.__table_name = table_name
        self.__db = db.Db.singleton()

        # clear link data
        self.__clear_link_data()

    def alias(self, alias):
        ''' 给主表起个别名, 这将影响到join条件中的字段名称 '''
        self.__alias = alias
        return self

    def where(self, *args, **kwargs):
        ''' where条件 '''
        self.__where_list.extend(args)

        if kwargs:
            self.__where_list.append(kwargs)

        return self

    ASC = 'ASC'
    DESC = 'DESC'

    def order(self, field, sequence=None):
        '''
            排序条件
            field: 字段名
            sequence: 排序顺序, DESC/ASC, 默认None
        '''
        self.__order_list.append((field, sequence))
        return self

    def limit(self, length):
        ''' limit参数 '''
        assert util.isInt(length)

        self.__limit = length
        return self

    def offset(self, offset):
        ''' offset参数 '''
        assert util.isInt(offset)

        self.__offset = offset
        return self

    LEFT = 'left'
    RIGHT = 'right'

    def join(self, table_name, on=None, alias=None, join_type=LEFT):
        '''
            连接表
            table_name:  表名
            on:          连接条件, 与where的格式相同
            alias:       别名, None表示不加别名, 默认为None
            join_type:   连接类型, left/right, 默认为left
        '''
        # check join type
        if join_type not in (self.LEFT, self.RIGHT):
            raise ValueError('no such join type: %s' % join_type)

        # join on
        if not isinstance(on, dict):
            raise TypeError(
                'join on param must be dict. got type: %s, value: %s' % (
                    on.__class__,
                    on
                )
            )

        if alias is None:
            alias = table_name

        self.__join_list.append({
            'table': table_name,
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
    REFLECT_YES = 'a'
    REFLECT_NO = 'n'
    REFLECT_IF_UNDEFINE_FIELDS = 'i'

    def select(self, fields=None, sql_options=None, query_options=dict(),
               field_reflect_type=REFLECT_YES,
               reflect_tables=None):
        '''
            构造select语句并执行
            fields:              返回的字段, 默认为空
                格式:
                    [
                        'column',
                        ('table', 'column'),
                        ...
                    ]
            sql_options:         select的选项, 默认为空
            query_options:       query的选项, 字典形式
                fetchone:        只获取一行数据, 默认为False
                bydict:          以字典形式返回查询结果, 默认为True
            field_reflect_type:  自动反射字段的方式
                REFLECT_YES:     反射表中的字段, 附加fields中指定的字段
                REFLECT_NO:      不反射表中的字段, 只查询fields中指定的字段
                REFLECT_IF_UNDEFINE_FIELDS:
                                 如果没有指定fields, 则反射;
                                 否则不反射
                默认为REFLECT_IF_UNDEFINE_FIELDS
            reflect_tables:      需要反射的表的alias名.
                                 如果为None, 表示所有表.
        '''
        # build strings
        option_string = self.__build_option_string(sql_options)
        field_string = self.__build_field_string(
            fields, field_reflect_type, reflect_tables
        )
        table_string = self.__build_table_string()
        join_string = self.__build_join_string()
        where_string = self.__build_where_string()
        order_string = self.__build_order_string()
        limit_string = self.__build_limit_string()
        group_string = self.__build_group_string()

        # query result
        result = self.__db.query(
            ("select{option}{field}\n"
             "from {table}{join}{where}{group}{order}{limit}").format(
                option=option_string,
                field=field_string,
                table=table_string,
                join=join_string,
                where=where_string,
                group=group_string,
                order=order_string,
                limit=limit_string
            ),
            self.__params,
            **query_options
        )

        # clear
        self.__clear_link_data()

        # return
        return result

    def find(self, *args, **kwargs):
        ''' 获取一条记录, 参数见select '''
        result = self.limit(1).select(*args, **kwargs)
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
            },
            field_reflect_type=self.REFLECT_NO
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
        result = self.select(sql_options=(self.SQL_CALC_FOUND_ROWS,))
        count = self.found_rows()
        return result, count

    def insert(self, *args, **kwargs):
        ''' 执行insert操作 '''
        params = dict()
        for arg in args:
            params.update(arg)

        if kwargs:
            params.update(kwargs)

        table_name = self.__db.table_prefix() + self.__table_name
        result = self.__db.execute(
            ('insert into {table} ({columns}) '
             'values ({values})').format(
                table=table_name,
                columns=','.join(
                    ['`' + col + '`' for col in params]
                ),
                values=','.join(
                    ['%%(%s)s' % col for col in params]
                )
            ),
            params
        )

        self.__clear_link_data()
        return result['last_insert_id']

    def update(self, *args, **kwargs):
        ''' 执行update操作 '''
        return result['row_count']

    def __clear_link_data(self):
        self.__alias = None
        self.__where_list = list()
        self.__order_list = list()
        self.__limit = None
        self.__offset = None
        self.__join_list = list()
        self.__group_list = list()
        self.__params = dict()

    def __build_option_string(self, options):
        if options:
            return ' ' + ' '.join(options)
        else:
            return ''

    def __get_column_list(self, table_name):
        cache = self.__class__.__cache

        if not 'show_columns' in cache:
            cache['show_columns'] = dict()

        columns = cache['show_columns']
        if table_name not in columns:
            columns[table_name] = [
                col['Field'] for col in self.__db.query(
                    "SHOW COLUMNS FROM `%s%s`" % (
                        self.__db.table_prefix(),
                        table_name
                    )
                )
            ]

        return columns[table_name]

    def __get_table_alias_list(self):
        '''
            返回所有的表以及表对应的alias
            由于表名可能会重复, 所以返回值只能是tuple的list
            [
                ('table_name', 'alias'),
                ...
            ]
        '''
        table_name_list = list()

        # self table
        table_name_list.append((
            self.__table_name,
            self.__alias if self.__alias else self.__table_name
        ))

        # join tables
        table_name_list.extend(
            [
                (join['table'], join['alias'])
                for join in self.__join_list
            ]
        )

        return table_name_list

    def __build_field_string(self, fields, field_reflect_type, reflect_tables):
        ''' 构建field语句, 直接用于select '''
        if field_reflect_type == self.REFLECT_IF_UNDEFINE_FIELDS:
            if fields:
                field_list = self.__build_field_list_by_fields(fields)
            else:
                field_list = self.__build_field_list_by_reflect(reflect_tables)
        elif field_reflect_type == self.REFLECT_YES:
            field_list = self.__build_field_list_by_reflect(reflect_tables)
            if fields:
                field_list.extend(
                    self.__build_field_list_by_fields(fields)
                )
        elif field_reflect_type == self.REFLECT_NO:
            assert not fields is None
            field_list = self.__build_field_list_by_fields(fields)
        else:
            raise ValueError('no such reflect type: %s' % field_reflect_type)

        return '\n' + ',\n'.join(field_list)

    def __build_field_list_by_fields(self, fields):
        '''
            通过指定的fields构建field list,
            fields参数格式参见select
        '''
        return [
            '`{table}`.`{column}` as `{table}.{column}`'.format(
                table=field[0],
                column=field[1]
            ) if isinstance(field, (list, tuple)) else field
            for field in fields
        ]

    def __build_field_list_by_reflect(self, reflect_tables):
        '''
            通过反射表的结构构建field list
            reflect_tables:    只反射指定的表的结构
                               如果为None, 反射全部表
        '''
        # table alias list
        table_alias_list = self.__get_table_alias_list()
        # filter by reflect tables
        if reflect_tables:
            reflect_tables = set(reflect_tables)
            table_alias_list = filter(
                lambda ta: ta[1] in reflect_tables,
                table_alias_list
            )

        # self table alias
        self_table_alias = self.__alias if self.__alias else self.__table_name

        # I am not sure the following code will work
        return [
            '`%s`.`%s`' % (
                alias, column
            ) if alias == self_table_alias else (
                '`{alias}`.`{column}` as `{alias}.{column}`'.format(
                    alias=alias,
                    column=column
                )
            )
            for table, alias in table_alias_list
            for column in self.__get_column_list(table)
        ]

    def __build_table_string(self):
        alias = self.__alias
        table_name = self.__db.table_prefix() + self.__table_name

        return '`%s` as %s' % (
            table_name,
            alias if alias else self.__table_name
        )

    def __build_join_string(self):
        table_prefix = self.__db.table_prefix()
        return ''.join([
            '\n' + '{join_type} join `{table}`{alias}{on}'.format(
                join_type=join['join_type'],
                table=table_prefix + join['table'],
                alias=' as %s' % join['alias'] if join['alias'] else '',
                on=' on (%s)' % (
                    self.__build_condition_string(join['on'])
                ) if join['on'] else ''
            )
            for join in self.__join_list
        ])

    def __build_where_string(self):
        if self.__where_list:
            return '\nwhere ' + ' AND '.join([
                self.__build_condition_string(where)
                for where in self.__where_list
            ])
        else:
            return ''

    # join的时候需要留个空格
    RELATION_AND = ' AND '
    RELATION_OR = ' OR '

    def __build_condition_string(self, condiction, relation=RELATION_AND):
        ''' 构建条件字符串 '''
        assert isinstance(condiction, dict)

        return relation.join([
            self.__build_condition_part(key, value)
            for key, value in condiction.iteritems()
        ])

    def __build_condition_part(self, key, value):
        ''' 构建条件字符串的一段 '''
        if key == '__or':
            if isinstance(value, dict):
                raise TypeError(
                    'value after `or` must be dict. got type:%s, value:%s' % (
                        value.__class__,
                        value
                    )
                )
            return '(%s)' % self.__build_condition_string(value, RELATION_OR)
        elif key == '__not':
            if isinstance(value, dict):
                raise TypeError(
                    'value after `not` must be dict. got type:%s, value:%s' % (
                        value.__class__,
                        value
                    )
                )
            return 'NOT(%s)' % self.__build_condition_string(value)
        else:
            # normal key
            # key as field name
            if isinstance(value, (basestring, int, long)):
                param_key = self.__add_param(key, value)
                return '%s = %%(%s)s' % (key, param_key)
            elif isinstance(value, tuple):
                operator, realvalue = value

                # switch operator
                if operator == 'in':
                    if isinstance(value, tuple):
                        raise TypeError(
                            ('value after `in` must be tuple.'
                             'got type:%s, value:%s') % (
                                value.__class__,
                                value
                            )
                        )

                    return '%s in (%s)' % (
                        key,
                        ','.join([
                            self.__add_param(
                                '%s_%d' % (key, i),
                                value_part
                            )
                            for i, value_part in enumerate(realvalue)
                        ])
                    )
                elif operator in ('=', '>', '<', '>=', '<='):
                    if isinstance(realvalue, FieldParam):
                        return '%s %s %s' % (
                            key,
                            relation,
                            realvalue.name
                        )
                    else:
                        return '%s %s %%(%s)s' % (
                            key,
                            relation,
                            self.__add_param(key, realvalue)
                        )
                else:
                    raise ValueError('unknown operator: %s' % operator)
            elif isinstance(value, FieldParam):
                return '%s = %s' % (key, value.name)
            else:
                raise TypeError(
                    'can not resolve value. type: %s, value: %s' % (
                        value.__class__,
                        value
                    )
                )

    def __build_order_string(self):
        if self.__order_list:
            return '\norder by ' + ','.join([
                '%s %s' % (
                    field, sequence
                ) if sequence else field
                for field, sequence in self.__order_list
            ])
        else:
            return ''

    def __build_limit_string(self):
        if self.__limit:
            if self.__offset:
                return '\nlimit %d, %d' % (
                    self.__offset,
                    self.__limit
                )
            else:
                return '\nlimit %d' % self.__limit
        else:
            return ''

    def __build_group_string(self):
        if self.__group_list:
            return '\ngroup by ' + ','.join(self.__group_list)
        else:
            return ''

    def __add_param(self, key, value):
        guess_length = 50

        if key in self.__params:
            for i in range(guess_length):
                guess_key = '%s_%d' % (key, i)

                if guess_key not in self.__params:
                    break

            if guess_length - 1 == i:
                raise ValueError('can not guess key for %s' % key)
            else:
                key = guess_key

        self.__params[key] = value
        return key


F = FieldParam
