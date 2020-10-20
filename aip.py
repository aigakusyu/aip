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
   params['freeword'] = "カレー"
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
