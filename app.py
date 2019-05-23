import os
import tempfile

from config import Config

from flask import Flask, request, abort, send_from_directory
from linebot.exceptions import LineBotApiError, InvalidSignatureError
from linebot.models import *

app = Flask(__name__)
config = Config(app)
line_bot_api = config.line_bot_api
handler = config.handler


@app.route('/callback', methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        handler.handle(body, signature)
    except LineBotApiError as e:
        print("Got exception from LINE Messaging API: %s\n" % e.message)
        for m in e.error.details:
            print("  %s: %s" % (m.property, m.message))
        print("\n")
    except InvalidSignatureError:
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    msg = event.message.text
    if msg == 'help':
        line_bot_api.reply_message(event.reply_token,
                                   TextSendMessage(text='1. Enter \'transcription on\' to turn on.\n'
                                                        '2. Enter \'transcription off\' to turn off.'))
    elif msg == 'transcription on':
        config.transcription_mode = True
        line_bot_api.reply_message(event.reply_token,
                                   TextSendMessage(text='Transcription Mode is turned ON.'))
    elif msg == 'transcription off':
        config.transcription_mode = False
        line_bot_api.reply_message(event.reply_token,
                                   TextSendMessage(text='Transcription Mode is turned OFF.'))


@handler.add(MessageEvent, message=(ImageMessage, VideoMessage, AudioMessage))
def handle_audio_message(event):
    print(event)
    app.logger.info('[receive type]', event.message.type)
    if isinstance(event.message, ImageMessage):
        ext = 'jpg'
    elif isinstance(event.message, VideoMessage):
        ext = 'mp4'
    elif isinstance(event.message, AudioMessage):
        ext = 'm4a'
    else:
        return

    message_content = line_bot_api.get_message_content(event.message.id)
    with tempfile.NamedTemporaryFile(dir=config.static_tmp_path, prefix=ext + '-', delete=False) as fp:
        for chunk in message_content.iter_content():
            fp.write(chunk)
        tmp_file_path = fp.name

    dist_path = tmp_file_path + '.' + ext
    dist_name = os.path.basename(dist_path)
    os.rename(tmp_file_path, dist_path)

    line_bot_api.reply_message(
        event.reply_token, [
            TextSendMessage(text='Save content.'),
            TextSendMessage(text=request.host_url + os.path.join('static', 'tmp', dist_name))
        ]
    )

    if not config.transcription_mode:
        return


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)




