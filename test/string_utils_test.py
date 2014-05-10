import unittest

from drape.util.string_utils import underscore

class StringUtilsTestCase(unittest.TestCase):
    def testSingleWord(self):
        self.assertEqual(
            underscore('Userinfo'),
            'userinfo'
        )

    def testDoubleWord(self):
        self.assertEqual(
            underscore('UserInfo'),
            'user_info'
        )

    def testMultiWord(self):
        self.assertEqual(
            underscore('UserSchoolStudent'),
            'user_school_student'
        )
