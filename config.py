import os
import sys

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
        self.transcription_mode = True

        self.__setup_channel()
        self.__create_static_tmp_dir()

    def __setup_channel(self):
        channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)
        channel_secret = os.getenv('LINE_CHANNEL_SECRET', None)

        if channel_access_token is None:
            self._app.logger('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
            sys.exit(1)

        if channel_secret is None:
            self._app.logger('Specify LINE_CHANNEL_SECRET as environment variable.')
            sys.exit(1)

        self.line_bot_api = LineBotApi(channel_access_token)
        self.handler = WebhookHandler(channel_secret)

    def __create_static_tmp_dir(self):
        self.static_tmp_path = os.path.join(os.path.dirname(__file__), 'static', 'tmp')
        os.makedirs(self.static_tmp_path, exist_ok=True)
