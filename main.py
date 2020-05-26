from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, ImageSendMessage, VideoSendMessage, StickerSendMessage, AudioSendMessage
)
import os
import random

import numpy as np

from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
db = SQLAlchemy(app)

#環境変数取得
LINE_CHANNEL_ACCESS_TOKEN = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
LINE_CHANNEL_SECRET = os.environ["LINE_CHANNEL_SECRET"]

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

#クラス指定
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_num = db.Column(db.Integer, unique=False)

    def __init__(self, user_num):
        self.user_num = user_num

class Bingo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bingo_num = db.Column(db.Integer, unique=False)

    def __init__(self, bingo_num):
        self.bingo_num = bingo_num

#関数指定
def is_bingo(finish_num):
    if finish_num == 0:
        return 1
    else:
        return 0

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    bingolist = [1, 2, 3, 4, 5, 6, 7, 8, 9]

    userNum = db.session.query(User).all()
    num = userNum[-1].user_num

    numnum = 0

    if "終了" in event.message.text:
        message = "終了です\n"

        if is_bingo(numnum) == 1:
            message += "ビンゴです！"

        number = 0
    elif "スタート" in event.message.text:
        random.shuffle(bingolist)

        message = "ビンゴ\n"
        n = 0

        for bin_num1 in bingolist:

            if n % 3 == 0:
                message += "\n"

            message += str(bin_num1)
            n += 1

        for bin_num2 in reversed(bingolist):
            bingo = Bingo(bin_num2)
            db.session.add(bingo)
            db.session.commit()

        number = 1
    elif "説明" in event.message.text:
        message = "ビンゴの説明"
    elif num == 1:
        bingolist = db.session.query(Bingo).all()
        message = "ビンゴ\n"
        binlis = []
        n = 0
        m = 0
        for bin_num in reversed(bingolist):
            if n % 3 == 0:
                message += "\n"

            message += str(bin_num.bingo_num)
            binlis.append(bin_num.bingo_num)
            n += 1

            if n == 9:
                break

        for i in binlis:
            if str(i) == event.message.text:
                binlis[binlis.index(i)] = 0
            m = 1

        if m == 1:
            for bin_num2 in reversed(binlis):
                bingo = Bingo(bin_num2)
                db.session.add(bingo)
                db.session.commit()

        number = 1
    else:
        message = "散歩ビンゴです。開始したい時は「スタート」やり方を知りたい時は「説明」と打ってね。"
        number = 0

    num = number
    user = User(num)
    db.session.add(user)
    db.session.commit()

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=message))


if __name__ == "__main__":
#    app.run()
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
