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

def is_bingo(finish_lists, finish_num):
    k = 0
    #縦判定
    for i in range(5):
        for j in range(4):
            if finish_lists[i] == finish_lists[i+(j+1)*5]:
                k += 1
        if k == 4:
            finish_num += 1
        k = 0

    #横判定
    for i in range(0,20,5):
        for j in range(4):
            if finish_lists[i] == finish_lists[i+1+j]:
                k += 1
        if k == 4:
            finish_num += 1
        k = 0

    #斜め判定
    for i in range(4):
        if finish_lists[0] == finish_lists[(i+1)*6]:
            k += 1
    if k == 4:
        finish_num += 1
    k = 0

    for i in range(4):
        if finish_lists[4] == finish_lists[4+(i+1)*4]:
            k += 1
    if k == 4:
        finish_num += 1
    k = 0

    return finish_num

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
    bingo_lists = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25]
    bingo_dicts = { '配達員':1, 'タピオカ':2, '噴水':3, '密':4, 'ジョギング':5,
                    'パトカー':6, 'カップル':7, '鳶':8, '黒マスク':9, '大きい石':10,
                    '犬':11, 'サンダル':12, '痛バッグ':13, 'ピンクの花':14, '日傘':15,
                    'マスク入荷':16, '足マーク':17, 'サッカーボール':18, 'ハンバーガー':19, 'インナーカラー':20,
                    '引っ越しトラック':21, '日本国旗':22, 'ゴミ袋カラス':23, 'ヘルメット通学':24, 'レシート':25 }
    userNum = db.session.query(User).all()
    num = userNum[-1].user_num

    numnum = 0

    if "終了" in event.message.text:
        message = "終了です\n"

        bingo_number = 0
        bingo_db = db.session.query(Bingo).all()
        bingo_lists = []
        n = 0

        for bin_num in reversed(bingo_db):
            bingo_lists.append(bin_num.bingo_num)
            n += 1

            if n == 25:
                break

        if is_bingo(bingo_lists, bingo_number) != 0:
            message += "{}つビンゴです！".format(is_bingo(bingo_lists, bingo_number))
        number = 0

    elif event.message.text == "スタート":
        random.shuffle(bingo_lists)

        im_tiles_line = []
        im_tiles = []

        k = 0
        for i in range(5):
            for j in range(5):
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
    elif num == 1:
        bingo_db = db.session.query(Bingo).all()
        message = "ビンゴ\n"
        bingo_lists = []
        n = 0
        m = 0
        for bin_num in reversed(bingo_db):
            bingo_lists.append(bin_num.bingo_num)
            n += 1

            if n == 25:
                break



        for bingo_dict_key, bingo_dict_value in bingo_dicts.items():
            if event.message.text in bingo_dicts_key:
                for bingo_list in bingo_lists:
                    if bingo_dict_value == bingo_list:
                        bingo_lists[bingo_lists.index(bingo_list)] = 0
                        m = 1

        n = 0

        im_tiles_line = []
        im_tiles = []

        k = 0
        for i in range(5):
            for j in range(5):
                im_path = cv2.imread("./static/images/" + str(bingo_lists[k]) + ".png")
                im_tiles_line.append(im_path)
                k += 1
            im_tiles.append(im_tiles_line)
            im_tiles_line = []

        im_tile = concat_tile(im_tiles)
        cv2.imwrite('./static/images/opencv_concat_tile.jpg', im_tile)

        if m == 1:
            for bin_num2 in reversed(bingo_lists):
                bingo = Bingo(bin_num2)
                db.session.add(bingo)
                db.session.commit()

        number = 1
    else:
        message = "散歩ビンゴです！\n開始したい時は「スタート」、終わりたい時は「終了」と打ってね！\n画像に書かれているものを見つけたら、その文字を入力してね！"
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
