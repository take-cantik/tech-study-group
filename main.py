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

app = Flask(__name__)

#環境変数取得
LINE_CHANNEL_ACCESS_TOKEN = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
LINE_CHANNEL_SECRET = os.environ["LINE_CHANNEL_SECRET"]

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

def is_finish(finish_num):
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
    bingolist = ["1", "2", "3", "4", "5", "6", "7", "8", "9"]
    number = 0

    if event.message.text == "スタート":
        message = "ビンゴ"
        random.shuffle(bingolist)

        for num in bingolist:
            if bingolist.index(num) % 3 == 0:
                message += "\n"
            message += num

    elif "説明" in event.message.text:
        message = "ビンゴの説明"
    elif is_finish(number) == 1:
        message = "終了です"
    else:
        message = "散歩ビンゴです。開始したい時は「スタート」やり方を知りたい時は「説明」と打ってね。"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=message))


if __name__ == "__main__":
#    app.run()
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
