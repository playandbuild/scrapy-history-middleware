import unittest
from datetime import datetime

from scrapy.conf import settings
from scrapy.exceptions import NotConfigured

from history.middleware import HistoryMiddleware


settings.overrides['HISTORY'] = {
    'S3_ACCESS_KEY': '',
    'S3_SECRET_KEY': '',
    'S3_BUCKET': '',
}


class TestHistoryMiddleware(unittest.TestCase):

    def setUp(self):
        self.middleware = HistoryMiddleware()

    def test_unconfigured_init(self):
        with self.assertRaises(NotConfigured):
            self.middleware = HistoryMiddleware(settings={})

    def test_parse_epoch(self):
        self.assertIsInstance(
            self.middleware.parse_epoch('yesterday'),
            datetime)
