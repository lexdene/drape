import unittest

class WithDemo(object):
    def __init__(self):
        self.data = 'asdfasdfasdf'

    def __enter__(self):
        return self

    def __exit__(self, errtype, value, trace):
        pass

class DemoTestCase(unittest.TestCase):
    def setUp(self):
        self.data = 1

    def tearDown(self):
        self.data = None

    def testData(self):
        self.assertEqual(self.data, 1)

    def testDataFail(self):
        self.assertEqual(self.data, 1)

    def testWithDemo(self):
        with WithDemo() as d:
            self.assertEqual(d.data, 'asdfasdfasdf')

        self.assertEqual(d.data, 'asdfasdfasdf')

    def testExceptElse(self):
        try:
            raise ValueError(1)
        except ValueError:
            self.assertTrue(True)
        else:
            self.assertTrue(False)
        finally:
            self.assertTrue(True)
