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
    print(event)
    msg = event.message.text
    msg = msg.lower()
    if msg == 'help':
        line_bot_api.reply_message(event.reply_token,
                                   TextSendMessage(text='1. Enter \"on\" to turn transcription on.\n'
                                                        '2. Enter \"off\" to turn transcription off.'))
    elif msg == 'on':
        config.transcription_mode = True
        line_bot_api.reply_message(event.reply_token,
                                   TextSendMessage(text='>> Transcription Mode is turned ON. <<'))
    elif msg == 'off':
        config.transcription_mode = False
        line_bot_api.reply_message(event.reply_token,
                                   TextSendMessage(text='>> Transcription Mode is turned OFF. <<'))


@handler.add(MessageEvent, message=AudioMessage)
def handle_audio_message(event):
    print(event)

    reply_messages = []
    message_content = line_bot_api.get_message_content(event.message.id)
    with tempfile.NamedTemporaryFile(dir=config.static_tmp_path, suffix='.m4a', delete=False) as fp:
        for chunk in message_content.iter_content():
            fp.write(chunk)

    if config.transcription_mode:
        text = transcribe(fp.name)
        os.remove(fp.name)

        if event.source.type == 'user':
            reply_messages.append(TextSendMessage(text=text))
        elif event.source.type == 'room':
            profile = line_bot_api.get_room_member_profile(event.source.room_id, event.source.user_id)
            reply_messages.append(TextSendMessage(text='【' + profile.display_name + '】說：\n' + text))
        elif event.source.type == 'group':
            profile = line_bot_api.get_group_member_profile(event.source.group_id, event.source.user_id)
            reply_messages.append(TextSendMessage(text='【' + profile.display_name + '】說：\n' + text))

    line_bot_api.reply_message(event.reply_token, reply_messages)


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)




