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

import cv2
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
def concat_tile(im_list_2d):
    return cv2.vconcat([cv2.hconcat(im_list_h) for im_list_h in im_list_2d])

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
    bingo_lists = [1, 2, 3, 4, 5, 6, 7, 8, 9]

    userNum = db.session.query(User).all()
    num = userNum[-1].user_num

    numnum = 0

    if "終了" in event.message.text:
        message = "終了です\n"

        if is_bingo(numnum) == 1:
            message += "ビンゴです！"

        number = 0
    elif "スタート" in event.message.text:
        random.shuffle(bingo_lists)

        im_tiles_line = []
        im_tiles = []

        k = 0
        for i in range(3):
            for j in range(3):
                im_path = cv2.imread("./static/images/" + str(bingo_lists[k]) + ".png")
                im_tiles_line.append(im_path)
                k += 1
            im_tiles.append(im_tiles_line)
            im_tiles_line = []

        im_tile = concat_tile(im_tiles)
        
        cv2.imwrite('./static/images/opencv_concat_tile.jpg', im_tile)
       
        for bin_num2 in reversed(bingo_lists):
            bingo = Bingo(bin_num2)
            db.session.add(bingo)
            db.session.commit() 

        number = 1
    elif "説明" in event.message.text:
        message = "ビンゴの説明"
    elif num == 1:
        bingo_lists = db.session.query(Bingo).all()
        message = "ビンゴ\n"
        binlis = []
        n = 0
        m = 0
        for bin_num in reversed(bingo_lists):
            binlis.append(bin_num.bingo_num)
            n += 1

            if n == 9:
                break

        for i in binlis:
            if str(i) == event.message.text:
                binlis[binlis.index(i)] = 0
            m = 1

        n = 0

        im_tiles_line = []
        im_tiles = []

        k = 0
        for i in range(3):
            for j in range(3):
                im_path = cv2.imread("./static/images/" + str(binlis[k]) + ".png")
                im_tiles_line.append(im_path)
                k += 1
            im_tiles.append(im_tiles_line)
            im_tiles_line = []

        im_tile = concat_tile(im_tiles)
        cv2.imwrite('./static/images/opencv_concat_tile.jpg', im_tile)

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

    if num == 1 or event.message.text == "スタート":
        line_bot_api.reply_message(
            event.reply_token,
            ImageSendMessage(
                original_content_url = "https://teruteruahuro.herokuapp.com/static/images/opencv_concat_tile.jpg",
                preview_image_url = "https://teruteruahuro.herokuapp.com/static/images/opencv_concat_tile.jpg"
            )
        )
    else:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=message))


if __name__ == "__main__":
#    app.run()
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
