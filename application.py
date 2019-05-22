import os
import sys
from flask import Flask, request, abort, send_from_directory

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import LineBotApiError, InvalidSignatureError
from linebot.models import *

__all__ = ['Application']


class Application(object):

    def __init__(self):
        self._app = Flask(__name__)
        self.__check_channel()
        self._app.add_url_rule('/callback', 'callback', self.callback, methods=['POST'])

    def __check_channel(self):
        channel_secret = os.getenv('LINE_CHANNEL_SECRET', None)
        channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)

        if channel_secret is None:
            self._app.logger('Specify LINE_CHANNEL_SECRET as environment variable.')
            sys.exit(1)

        if channel_access_token is None:
            self._app.logger('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
            sys.exit(1)

        self._line_bot_api = LineBotApi(channel_access_token)
        self._handler = WebhookHandler(channel_secret)

    def run(self, **kwargs):
        self._app.run(**kwargs)

    def callback(self):
        signature = request.headers['X-Line-Signature']
        body = request.get_data(as_text=True)
        self._app.logger.info("Request body: " + body)

        try:
            self._handler.handle(body, signature)
        except LineBotApiError as e:
            print("Got exception from LINE Messaging API: %s\n" % e.message)
            for m in e.error.details:
                print("  %s: %s" % (m.property, m.message))
            print("\n")
        except InvalidSignatureError:
            abort(400)

        return 'OK'
