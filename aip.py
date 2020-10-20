import sys
import json
import os
from flask import Flask, request, abort, send_file
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
   CarouselColumn, CarouselTemplate, FollowEvent,
   LocationMessage, MessageEvent, TemplateSendMessage,
   TextMessage, TextSendMessage, UnfollowEvent, URITemplateAction
)
import requests
import urllib.parse

app = Flask(__name__)

channel_secret = os.environ['channel_secret']
channel_access_token = os.environ['channel_access_token']
gurunavi_api = os.environ['gurunavi_api']

line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret) #その他
no_hit_message = "近くにお店がないみたいです"
DAMMY_URL = "https://canbus.com/blog/wp-content/uploads/2018/02/2015-tenpo.jpg"

@app.route("/")
def hello_world():
  return "hello world!"

@app.route("/callback", methods=['POST'])
def callback():
   signature = request.headers['X-Line-Signature']
   body = request.get_data(as_text=True)
   app.logger.info("Request body: " + body)
   try:
       handler.handle(body, signature)
   except InvalidSignatureError:
       abort(400)
   return 'OK'

def search_rest(lat, lon):
   url = "https://api.gnavi.co.jp/RestSearchAPI/v3/"
   params = {}
   params['latitude'] = lat
   params['longitude'] = lon
   params['keyid'] = gurunavi_api
   params['range'] = 3
   params['freeword'] = (a)
   response = requests.get(url, params)
   results = response.json()
   if "error" in results:
       if "message" in results:
           raise Exception("{}".format(results["message"]))
       else:
           raise Exception(DEF_ERR_MESSAGE)
   total_hit_count = results.get("total_hit_count", 0)
   if total_hit_count < 1:
       raise Exception(no_hit_message)
   return results

@handler.add(MessageEvent, message=LocationMessage)
def handle_location_message(event):
   list = []
   user_lat = event.message.latitude
   user_longit = event.message.longitude
   rest_result = search_rest(user_lat, user_longit)
   for rest in rest_result.get("rest"):
       image_url = rest.get("image_url", {})
       image1 = image_url.get("shop_image1", "thumbnail_template.jpg")
       if image1 == "":
           image1 = DAMMY_URL
       name = rest.get("name", "")
       url = rest.get("url", "")
       pr = rest.get("pr", "")
       pr_short = "以下、内容\n" + pr.get("pr_short", "")
       if len(pr_short) >= 60:
           pr_short = pr_short[:56] + "…"


       result_dict = {
               "thumbnail_image_url": image1,
               "title": name,
               "text": pr_short,
               "actions": {
                   "label": "ぐるなびで見る",
                   "uri": url
               }
           }
       list.append(result_dict)
   print(list)
   columns = [
       CarouselColumn(
           thumbnail_image_url=column["thumbnail_image_url"],
           title=column["title"],
           text=column["text"],
           actions=[
               URITemplateAction(
                   label=column["actions"]["label"],
                   uri=column["actions"]["uri"],
               )
           ]
       )
       for column in list
   ]

   messages = TemplateSendMessage(
       alt_text="お近くのカレー屋さんについて連絡しました。",
       template=CarouselTemplate(columns=columns),
   )
   line_bot_api.reply_message(event.reply_token, messages=messages)


if __name__ == "__main__":
   port = int(os.getenv("PORT", 5000))
   app.run(host="0.0.0.0", port=port)
