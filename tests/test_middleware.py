import unittest

from history.middleware import HistoryMiddleware


class TestHistoryMiddleware(unittest.TestCase):

    def setUp(self):
        self.middleware = HistoryMiddleware()
        print self.middleware

    def test_spider_opened(self):
        pass
