import os
import tempfile

from config import Config
from util.transcription import transcribe

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
    elif msg == 'on':
        config.transcription_mode = True
        line_bot_api.reply_message(event.reply_token,
                                   TextSendMessage(text='Transcription Mode is turned ON.'))
    elif msg == 'off':
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

    reply_messages = []
    message_content = line_bot_api.get_message_content(event.message.id)
    with tempfile.NamedTemporaryFile(dir=config.static_tmp_path, suffix='.' + ext, delete=False) as fp:
        for chunk in message_content.iter_content():
            fp.write(chunk)
        dst_path = fp.name
        dst_name = os.path.basename(dst_path)
        reply_messages.append(TextSendMessage(text='Save content.'))
        reply_messages.append(TextSendMessage(text=request.host_url + os.path.join('static', 'tmp', dst_name)))

    # transcription mode is ON
    if ext == 'm4a' and config.transcription_mode:
        text = transcribe(dst_path)
        reply_messages.append(TextSendMessage(text=text))

    line_bot_api.reply_message(event.reply_token, reply_messages)


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)




