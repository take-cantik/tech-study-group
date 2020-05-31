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
import time
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
    user_id = db.Column(db.String(80), unique=False)
    user_num = db.Column(db.Integer, unique=False)
    bingo_num = db.Column(db.String(180), unique=False)
    time_second = db.Column(db.Integer, unique=False)

    def __init__(self, user_id, user_num, bingo_num, time_second):
        self.user_id = user_id
        self.user_num = user_num
        self.bingo_num = bingo_num
        self.time_second = time_second

#関数指定
def concat_tile(im_list_2d):
    return cv2.vconcat([cv2.hconcat(im_list_h) for im_list_h in im_list_2d])

def is_bingo(finish_lists, finish_num):
    k = 0
    #縦判定
    for i in range(5):
        for j in range(0, 21, 5):
            if finish_lists[i + j] > 100:
                k += 1
        if k == 5:
            finish_num += 1
        k = 0

    #横判定
    for i in range(0, 21, 5):
        for j in range(5):
            if finish_lists[i + j] > 100:
                k += 1
        if k == 5:
            finish_num += 1
        k = 0

    #斜め判定
    for i in range(0, 25, 6):
        if finish_lists[i] > 100:
            k += 1
    if k == 5:
        finish_num += 1
    k = 0

    for i in range(4, 21, 4):
        if finish_lists[i] > 100:
            k += 1
    if k == 5:
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
    profile = line_bot_api.get_profile(event.source.user_id)

    user_info = db.session.query(User).all()

    check_used = 0
    for user_info_id in reversed(user_info):
        if profile.user_id == user_info_id.user_id:
            profile = user_info_id
            check_used += 1
            break

    if check_used == 1:
        num = profile.user_num
    else:
        num = 0

    bingo_lists = [ 1, 2, 3, 4, 5, 6, 7, 8, 9, 10,
                    11, 12, 13, 14, 15, 16, 17, 18, 19, 20,
                    21, 22, 23, 24, 25, 26, 27, 28, 29, 30,
                    31, 32, 33, 34, 35, 36, 37, 38 ]

    bingo_dicts = { '配達員':1, 'タピオカ':2, '噴水':3, '密':4, 'ジョギング':5,
                    'パトカー':6, 'カップル':7, '鳶':8, '黒マスク':9, '大きい石':10,
                    '犬':11, 'サンダル':12, '痛バッグ':13, 'ピンクの花':14, '日傘':15,
                    'マスク入荷':16, '足マーク':17, 'サッカーボール':18, 'ハンバーガー':19, 'インナーカラー':20,
                    '引っ越しトラック':21, '日本国旗':22, 'ゴミ袋カラス':23, 'ヘルメット通学':24, 'レシート':25,
                    '車内タバコ':26, '救急車':27, '飛行機雲':28, '猫':29, '国道標識':30,
                    '移動販売車':31, '数字の7':32, '数字の1':33, 'バイク':34, '工事作業員':35,
                    '蜘蛛の巣':36, '監視カメラ':37, '宇宙人':38 }

    is_video = 0

    if "終了" in event.message.text and num == 1:
        finish_time = int(time.time())
        start_time = profile.time_second

        message = "終了です\n"

        bingo_lists = [int(x.strip()) for x in profile.bingo_num.split(',')]

        finish_time -= start_time
        message += "あなたの散歩時間は"
        finish_hour = finish_time//3600
        finish_minite = finish_time%3600//60
        finish_second = finish_time%3600%60

        if finish_hour > 0:
            message += "{0}時間{1}分{2}秒でした\n".format(finish_hour, finish_minite, finish_second)
        elif finish_minite > 0:
            message += "{0}分{1}秒でした\n".format(finish_minite, finish_second)
        else:
            message += "{0}秒でした\n".format(finish_second)

        if finish_minite < 20 and finish_hour < 1:
            message += "もう少し散歩しましょう！\n"
        elif finish_hour < 1:
            message += "散歩お疲れ様でした！\n"
        else:
            message += "よく頑張りました\nお疲れ様でした！\n"

        bingo_number = 0

        if is_bingo(bingo_lists, bingo_number) != 0:
            message += "{}つビンゴです！".format(is_bingo(bingo_lists, bingo_number))

            video_url = "https://teruteruahuro.herokuapp.com/static/videos/" + str(is_bingo(bingo_lists, bingo_number) // 4) + ".MP4"
            preview_url = "https://teruteruahuro.herokuapp.com/static/images/" + str(is_bingo(bingo_lists, bingo_number) // 4) + ".jpg"

            is_video = 1
        else:
            message += "残念！ビンゴならず"

        if is_bingo(bingo_lists,bingo_number) >= 8 and finish_minite < 5 and finish_hour < 1:
            message += "\nチートしませんでしたか？？？？？"

        number = 0

    elif event.message.text == "スタート":
        profile.time_second = int(time.time())

        random.shuffle(bingo_lists)
        del bingo_lists[-13:]

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
        im_time = int(time.time())
        image_url = './static/images/' + str(im_time) + '.jpg'

        cv2.imwrite(image_url, im_tile)

        number = 1
    elif num == 1:
        bingo_lists = [int(x.strip()) for x in profile.bingo_num.split(',')]

        message = "ビンゴ\n"

        for bingo_dict_key, bingo_dict_value in bingo_dicts.items():
            if bingo_dict_key in event.message.text:
                for bingo_list in bingo_lists:
                    if bingo_dict_value == bingo_list:
                        bingo_lists[bingo_lists.index(bingo_list)] += 100

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
        im_time = int(time.time())
        image_url = './static/images/' + str(im_time) + '.jpg'

        cv2.imwrite(image_url, im_tile)

        number = 1
    else:
        message = "散歩ビンゴです！\n開始したい時は「スタート」、終わりたい時は「終了」と打ってね！\n画像に書かれているものを見つけたら、その文字を入力してね！"
        number = 0

    num = number
    bingo_lists_str = map(str, bingo_lists)
    bingo_lists = ','.join(bingo_lists_str)
    if check_used == 1:
        time_db = profile.time_second
    else:
        time_db = 0

    user = User(profile.user_id, num, bingo_lists, time_db)
    db.session.add(user)
    db.session.commit()

    if num == 1 or event.message.text == "スタート":
        images_url = 'https://teruteruahuro.herokuapp.com/static/images/' + str(im_time) + '.jpg'

        line_bot_api.reply_message(
            event.reply_token,
            ImageSendMessage(
                original_content_url=images_url,
                preview_image_url=images_url
            )
        )
    elif is_video == 1:
        line_bot_api.reply_message(
            event.reply_token,
            [TextSendMessage(text=message),
            VideoSendMessage(
                original_content_url = video_url,
                preview_image_url = preview_url
            )]
        )
    else:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=message)
        )

if __name__ == "__main__":
#    app.run()
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
