import unittest

from drape.sql import builder, db, table

db_obj = None

def setUp(self):
    global db_obj
    connect_args = {
        'user': 'drape_test_user',
        'password': 'drape_test_123456',
        'database': 'drape_test',
        'autocommit': True,
    }

    db_obj = db.Db(connect_args)

    table.create_table(db_obj, UserInfo(), force=True)

def tearDown(self):
    table.drop_table(db_obj, UserInfo())

class UserInfo(table.Table):
    def _define(self):
        self.primary_id()
        self.string('username', null=False)

class ModelTestCase(unittest.TestCase):
    def testModel(self):
        user_builder = builder.LinkedBuilder(UserInfo(), db_obj)
        self.assertEqual(
            'select\n'
            '`user_infos`.`id`,\n'
            '`user_infos`.`username`\n'
            'from `user_infos` as user_infos',
            user_builder.select(return_sql=True)
        )

    def testTransaction(self):
        user_builder = builder.LinkedBuilder(UserInfo(), db_obj)
        with db_obj.transaction():
            user_builder.insert(
                username='elephant'
            )
            self.assertEqual(1, user_builder.count())

        self.assertEqual(1, user_builder.count())

        try:
            with db_obj.transaction():
                user_builder.insert(
                    username='elephant2',
                )
                self.assertEqual(2, user_builder.count())

                raise ValueError('to break transaction')
        except ValueError:
            self.assertTrue(True)
        else:
            self.assertTrue(False)

        self.assertEqual(1, user_builder.count())
