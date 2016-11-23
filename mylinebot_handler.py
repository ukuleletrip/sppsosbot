#! /usr/bin/env python
# -*- coding:utf-8 -*-
#
# you have to install Beautifulsoup.
# $ mkdir libs
# $ pip install -t libs beautifulsoup4


"""Callback Handler from LINE Bot platform"""

__author__ = 'ukuleletrip@gmail.com (Ukulele Trip)'

#import sys
#sys.path.insert(0, 'libs')
import webapp2
from google.appengine.api import urlfetch
import json
import logging
from appkeys import APP_KEYS
from datetime import datetime, timedelta
import hmac, hashlib, base64

class LineBotAPI(object):
    APIURL = 'https://api.line.me'

    def __init__(self, token):
        self.token = token

    def replyMessage(self, msg, reply_token):
        url = self.APIURL + '/v2/bot/message/reply'
        result = urlfetch.fetch(
            url=url,
	    method=urlfetch.POST, 
	    headers={'Content-Type':'application/json',
                     'Authorization':'Bearer %s' % (self.token)
            },
	    payload=json.dumps({
	        'replyToken' : reply_token,
	        'messages' : [
                    { 'type' : 'text',
                      'text' : msg.encode('utf-8')}
                ]
            })
        )
        logging.debug(result.content)


def is_valid_signature(request):
    signature = base64.b64encode(hmac.new(APP_KEYS['line']['secret'],
                                          request.body,
                                          hashlib.sha256).digest())
    return signature == request.headers.get('X-LINE-Signature')

class BotCallbackHandler(webapp2.RequestHandler):
    def post(self):
        logging.debug('kick from line server,\n %s' % self.request.body)
        params = json.loads(self.request.body)

        line_bot_api = LineBotAPI(APP_KEYS['line']['token'])

        if is_valid_signature(self.request):
            recv_msg = params['events'][0]
            line_bot_api.replyMessage(recv_msg['message']['text'],
                                      recv_msg['replyToken'])

        return self.response.write(json.dumps({}))



# I've decided not to use line SDK because...
'''
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)

line_bot_api = LineBotApi(APP_KEYS['line']['token']o)
handler = WebhookHandler(APP_KEYS['line']['secret'])

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=event.message.text))

class BotCallbackHandler(webapp2.RequestHandler):
    def post(self):
        signature = self.request.headers.get('X-Line-Signature')

        # handle webhook body
        logging.debug('kick from line server,\n %s' % self.request.body)
        try:
            body = self.request.body.decode('utf-8')
            handler.handle(body, signature)
        except InvalidSignatureError:
            abort(400)

        return 'OK'
'''
