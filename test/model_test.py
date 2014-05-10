import unittest

from drape.sql import builder, db, table

db_obj = None

def setUp(self):
    global db_obj
    connect_args = {
        'user': 'drape_test_user',
        'password': 'drape_test_123456',
        'database': 'drape_test'
    }

    db_obj = db.Db(connect_args)

    table.create_table(db_obj, UserInfo())

class UserInfo(table.Table):
    def _define(self):
        self.string('username', null=False)
        self.meta_times()

class ModelTestCase(unittest.TestCase):
    def testModel(self):
        user_builder = builder.LinkedBuilder(UserInfo(), db_obj)
        self.assertEqual(
            'select\n'
            '`user_infos`.`id`,\n'
            '`user_infos`.`username`,\n'
            '`user_infos`.`created_at`,\n'
            '`user_infos`.`updated_at`\n'
            'from `user_infos` as user_infos',
            user_builder.select(return_sql=True)
        )
