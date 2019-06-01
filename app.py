import os
import tempfile
import hashlib

from config import Config
from util.transcription import transcribe

from boto3.dynamodb.conditions import Key, Attr
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

    is_on = None
    if msg == 'help':
        line_bot_api.reply_message(event.reply_token,
                                   TextSendMessage(text='1. Enter \"on\" to turn transcription on.\n'
                                                        '2. Enter \"off\" to turn transcription off.'))
    elif msg == 'on':
        is_on = True
        line_bot_api.reply_message(event.reply_token,
                                   TextSendMessage(text='>> Transcription Mode is turned ON. <<'))
    elif msg == 'off':
        is_on = False
        line_bot_api.reply_message(event.reply_token,
                                   TextSendMessage(text='>> Transcription Mode is turned OFF. <<'))

    if is_on is not None:
        sha256_id = None
        if event.source.type == 'user':
            user_id = event.source.user_id
            sha256_id = hashlib.sha256(user_id.encode()).hexdigest()
        elif event.source.type == 'room':
            room_id = event.source.room_id
            sha256_id = hashlib.sha256(room_id.encode()).hexdigest()
        elif event.source.type == 'group':
            group_id = event.source.group_id
            sha256_id = hashlib.sha256(group_id.encode()).hexdigest()

        if sha256_id:
            config.table.update_item(
                Key={
                    'id': sha256_id,
                },
                UpdateExpression='SET is_on = :is_on',
                ExpressionAttributeValues={
                    ':is_on': is_on
                }
            )


@handler.add(JoinEvent)
def handle_join_event(event):
    print(event)

    sha256_id = None
    if event.source.type == 'user':
        user_id = event.source.user_id
        sha256_id = hashlib.sha256(user_id.encode()).hexdigest()
    elif event.source.type == 'room':
        room_id = event.source.room_id
        sha256_id = hashlib.sha256(room_id.encode()).hexdigest()
    elif event.source.type == 'group':
        group_id = event.source.group_id
        sha256_id = hashlib.sha256(group_id.encode()).hexdigest()

    if sha256_id is not None:
        config.table.put_item(
            Item={
                'id': sha256_id,
                'type': event.source.type,
                'is_on': True
            }
        )

        line_bot_api.reply_message(event.reply_token,
                                   TextSendMessage(text='Enter \"help\" to catch more information.'))


@handler.add(LeaveEvent)
def handle_leave_event(event):
    print(event)

    sha256_id = None
    if event.source.type == 'user':
        user_id = event.source.user_id
        sha256_id = hashlib.sha256(user_id.encode()).hexdigest()
    elif event.source.type == 'room':
        room_id = event.source.room_id
        sha256_id = hashlib.sha256(room_id.encode()).hexdigest()
    elif event.source.type == 'group':
        group_id = event.source.group_id
        sha256_id = hashlib.sha256(group_id.encode()).hexdigest()

    if sha256_id is not None:
        config.table.delete_item(
            Key={
                'id': sha256_id
            }
        )


@handler.add(MessageEvent, message=AudioMessage)
def handle_audio_message(event):
    print(event)

    reply_messages = []

    sha256_id = None
    if event.source.type == 'user':
        user_id = event.source.user_id
        sha256_id = hashlib.sha256(user_id.encode()).hexdigest()
    elif event.source.type == 'room':
        room_id = event.source.room_id
        sha256_id = hashlib.sha256(room_id.encode()).hexdigest()
    elif event.source.type == 'group':
        group_id = event.source.group_id
        sha256_id = hashlib.sha256(group_id.encode()).hexdigest()

    response = config.table.query(
        KeyConditionExpression=Key('id').eq(sha256_id)
    )

    print(response)
    if sha256_id is not None and response['Count'] > 0 and response['Items'][0]['is_on']:
        message_content = line_bot_api.get_message_content(event.message.id)
        with tempfile.NamedTemporaryFile(dir=config.static_tmp_path, suffix='.m4a', delete=False) as fp:
            for chunk in message_content.iter_content():
                fp.write(chunk)

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
