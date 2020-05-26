from flask import Flask, request, abort
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, ImageSendMessage, VideoSendMessage, StickerSendMessage
)
import random
import os

import numpy as np
import cv2
app = Flask(__name__)
#環境変数取得
LINE_CHANNEL_ACCESS_TOKEN = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
LINE_CHANNEL_SECRET = os.environ["LINE_CHANNEL_SECRET"]
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

def concat_tile(im_list_2d):
    return cv2.vconcat([cv2.hconcat(im_list_h) for im_list_h in im_list_2d])

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

    im_tiles_line = []
    im_tiles = []

    k = 0
    for i in range(3):
        for j in range(3):
            im_path = cv2.imread("images/" + str(bingo_lists[k]) + ".png")
            im_tiles_line.append(im_path)
            k += 1
        im_tiles.append(im_tiles_line)

    im_tile = concat_tile(im_tiles)
    import glob
    print(glob.glob("./*"))
    cv2.imwrite('images/opencv_concat_tile.jpg', im_tile)

    line_bot_api.reply_message(
        event.reply_token,
        ImageSendMessage(
            original_content_url = "https://teruteruahuro.herokuapp.com/images/opencv_concat_tile.jpg",
            preview_image_url = "https://teruteruahuro.herokuapp.com/images/opencv_concat_tile.jpg"
        )
    )

if __name__ == "__main__":
#    app.run()
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
