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

    if "スタート" in event.message.text:
        random.shuffle(bingolist)

        message = "ビンゴ\n"
        n = 0

        for bin_num in reversed(bingolist):
            bingo = Bingo(bin_num)
            db.session.add(bingo)
            db.session.commit()

            if n % 3 == 0:
                message += "\n"

            message += str(bin_num)
            n += 1

        number = 1
    elif num == 1:
        bingolist = db.session.query(Bingo).all()
        message = "ビンゴ\n"
        n = 0
        for bin_num in reversed(bingolist.bingo_num):
            if n % 3 == 0:
                message += "\n"

            message += str(bin_num)
            n += 1

        number = 0
    else:
        message = "ビンゴができるお"
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
