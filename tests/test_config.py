import os
import unittest

from linebot import (
    SignatureValidator, WebhookParser, WebhookHandler
)
from config import Config
from flask import Flask, request, abort, send_from_directory


class TestConfig(unittest.TestCase):
    def setUp(self) -> None:
        os.environ['LINE_CHANNEL_ACCESS_TOKEN'] = 'LINE_CHANNEL_ACCESS_TOKEN'
        os.environ['LINE_CHANNEL_SECRET'] = 'LINE_CHANNEL_SECRET'
        os.environ['AWS_ACCESS_KEY_ID'] = 'AWS_ACCESS_KEY_ID'
        os.environ['AWS_SECRET_ACCESS_KEY'] = 'AWS_SECRET_ACCESS_KEY'
        os.environ['AWS_TABLE_NAME'] = 'AWS_TABLE_NAME'

        app = Flask('channel_secret')
        self._config = Config(app)

    def test_static_tmp_dir(self) -> None:
        self.assertTrue(os.path.isdir(self._config.static_tmp_path))
        self.assertEqual(os.path.basename(self._config.static_tmp_path), 'tmp')

        prev_path = os.path.dirname(self._config.static_tmp_path)
        self.assertTrue(os.path.isdir(prev_path))
        self.assertEqual(os.path.basename(prev_path), 'static')


if __name__ == '__main__':
    unittest.main()
