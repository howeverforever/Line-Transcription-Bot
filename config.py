import os
import sys
import boto3

from linebot import LineBotApi, WebhookHandler


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Config(metaclass=Singleton):
    def __init__(self, app):
        self._app = app

        self.__setup_channel()
        self.__connect_database()
        self.__create_static_tmp_dir()

    def __setup_channel(self):
        channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)
        channel_secret = os.getenv('LINE_CHANNEL_SECRET', None)

        if channel_access_token is None:
            self._app.logger.info('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
            sys.exit(1)

        if channel_secret is None:
            self._app.logger.info('Specify LINE_CHANNEL_SECRET as environment variable.')
            sys.exit(1)

        self.line_bot_api = LineBotApi(channel_access_token)
        self.handler = WebhookHandler(channel_secret)

    def __connect_database(self):
        aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID', None)
        aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY', None)
        aws_table_name = os.getenv('AWS_TABLE_NAME', None)

        if aws_access_key_id is None:
            self._app.logger.info('Specify AWS_ACCESS_KEY_ID as environment variable.')
            sys.exit(1)

        if aws_secret_access_key is None:
            self._app.logger.info('Specify AWS_SECRET_ACCESS_KEY as environment variable.')
            sys.exit(1)

        if aws_secret_access_key is None:
            self._app.logger('Specify AWS_TABLE_NAME as environment variable.')
            sys.exit(1)

        self.table = boto3.resource('dynamodb', region_name='ap-southeast-1').Table(aws_table_name)

    def __create_static_tmp_dir(self):
        self.static_tmp_path = os.path.join(os.path.dirname(__file__), 'static', 'tmp')
        os.makedirs(self.static_tmp_path, exist_ok=True)
