import unittest

from drape.sql import table

class UserInfo(table.Table):
    def _define(self):
        self.primary_id()
        self.string('username', null=False)
        self.integer('age', null=False)
        self.meta_times()

class MockDb:
    def __init__(self):
        self.__last_sql = ''

    def execute(self, sql, params=None):
        self.__last_sql = sql

    def last_sql(self):
        return self.__last_sql

class CreateTableTestCase(unittest.TestCase):
    def testCreateTable(self):
        db_obj = MockDb()
        table.create_table(db_obj, UserInfo())
        self.assertEqual(
            (
                'CREATE TABLE IF NOT EXISTS `user_infos`('
                '`id` INT NOT NULL AUTO_INCREMENT,'
                '`username` VARCHAR(100) NOT NULL,'
                '`age` INT NOT NULL,'
                '`created_at` DATETIME NOT NULL,'
                '`updated_at` DATETIME NOT NULL,'
                'PRIMARY KEY(`id`)'
                ')ENGINE=InnoDB DEFAULT CHARSET=utf8'
            ),
            db_obj.last_sql()
        )
