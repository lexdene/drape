import itertools
from enum import Enum
import re

from ..util.string_utils import pluralize, underscore

ColumnTypes = Enum(
    'ColumnTypes',
    'INT BOOLEAN VARCHAR DATETIME TIME ENUM',
    module=__name__
)

IndexTypes = Enum(
    'IndexTypes',
    'PRIMARY UNIQUEY',
    module=__name__
)

class Column:
    def __init__(self, name, column_type,
                 type_desc=None, null=True,
                 auto_increment=False):
        self.name = name
        self.column_type = column_type
        self.type_desc = type_desc
        self.null = null
        self.auto_increment = auto_increment

class Index:
    def __init__(self, name, index_type):
        self.name = name
        self.index_type = index_type

class Table:
    def __init__(self):
        self.create_primary_id = True
        self.__columns = []
        self.__indexes = []

        self._define()

    def _define(self):
        'rewrite this method in subclass to define table'
        pass

    @property
    def table_name(self):
        return pluralize(
            underscore(
                re.sub(
                    r'Table^',
                    '',
                    self.__class__.__name__
                )
            )
        )

    @property
    def engine(self):
        return 'InnoDB'

    @property
    def charset(self):
        return 'utf8'

    def columns(self):
        return self.__columns

    def indexes(self):
        return self.__indexes

    def integer(self, name, null=True, auto_increment=False):
        self.__columns.append(
            Column(
                name=name,
                column_type=ColumnTypes.INT,
                null=null,
                auto_increment=auto_increment
            )
        )

    def string(self, name, length=100, null=True):
        self.__columns.append(
            Column(
                name=name,
                column_type=ColumnTypes.VARCHAR,
                type_desc=length,
                null=null
            )
        )

    def datetime(self, name, null=True):
        self.__columns.append(
            Column(
                name=name,
                column_type=ColumnTypes.DATETIME,
                null=null
            )
        )

    def add_index(self, *argv, **kwargs):
        self.__indexes.append(Index(*argv, **kwargs))

    def primary_id(self):
        self.integer('id', null=False, auto_increment=True)
        self.add_index('id', IndexTypes.PRIMARY)

    def meta_times(self):
        self.datetime('created_at', null=False)
        self.datetime('updated_at', null=False)


def create_table(db_obj, table, force=False):
    sql = (
        'CREATE TABLE {force} `{table_name}`('
        '{define}'
        ')ENGINE={engine} DEFAULT CHARSET={charset}'
    ).format(
        force='' if force else 'IF NOT EXISTS',
        table_name=table.table_name,
        define=','.join(
            itertools.chain(
                _create_columns_sql(table),
                _create_index_sql(table)
            )
        ),
        engine=table.engine,
        charset=table.charset
    )

    db_obj.execute(sql)

def _create_columns_sql(table):
    for column in table.columns():
        yield '`{name}` {column_type}{type_desc} {null}{auto_increment}'.format(
            name=column.name,
            column_type=column.column_type.name,
            type_desc='(%s)' % column.type_desc if column.type_desc else '',
            null='' if column.null else 'NOT NULL',
            auto_increment=' AUTO_INCREMENT' if column.auto_increment else ''
        )

def _create_index_sql(table):
    for index in table.indexes():
        yield '{index_type} KEY(`{name}`)'.format(
            index_type=index.index_type.name,
            name=index.name
        )
