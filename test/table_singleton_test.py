import unittest

from drape.sql import table


class UserInfo(table.Table):
    def _define(self):
        self.primary_id()
        self.string('username', null=False)


class LoginInfo(table.Table):
    def _define(self):
        self.primary_id()
        self.string('login_name', null=False)
        self.string('password', null=False)


class TableSingletonTestCase(unittest.TestCase):
    def testSingleton(self):
        a = UserInfo()
        b = UserInfo()
        c = LoginInfo()

        self.assertEqual(
            id(a),
            id(b)
        )
        self.assertNotEqual(
            id(a),
            id(c)
        )
        self.assertNotEqual(
            id(b),
            id(c)
        )
