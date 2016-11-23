#! /usr/bin/env python
# -*- coding:utf-8 -*-
#

"""Callback Handler from LINE Bot platform"""

__author__ = 'ukuleletrip@gmail.com (Ukulele Trip)'

#import sys
#sys.path.insert(0, 'libs')
import webapp2
import json
import logging
from appkeys import APP_KEYS
from datetime import datetime, timedelta
from linebotapi import LineBotAPI, WebhookRequest, is_valid_signature
from sosapi import SOSAPI
from tzimpl import JST, UTC

tz_jst = JST()
tz_utc = UTC()

class BotCallbackHandler(webapp2.RequestHandler):
    def post(self):
        logging.debug('kick from line server,\n %s' % self.request.body)

        recv_req = WebhookRequest(self.request.body)
        line_bot_api = LineBotAPI(APP_KEYS['line']['token'])

        if is_valid_signature(APP_KEYS['line']['secret'],
                              self.request.headers.get('X-LINE-Signature'),
                              self.request.body):
            
            if recv_req.is_text_message():
                sos_api = SOSAPI(APP_KEYS['SOS']['token'], APP_KEYS['SOS']['url'])
                recv_msg = recv_req.get_message()
                sensor_name = sos_api.get_sensor_name(recv_msg)

                if sensor_name:
                    value = sos_api.get_last_sensor_value('NagoyaU-Farm',
                                                          'WeatherStation-LUFFT',
                                                          sensor_name)
                    now = datetime.now()
                    td = now - value['datetime']
                    td_min = (td.seconds + td.days*24*3600)/60
                    before_str = ' (%d min before)' % (td_min) if td_min > 1 else ''

                    line_bot_api.replyMessage('%.1f %s%s' % (value['value'],
                                                             value['unit'],
                                                             before_str),
                                              recv_req.get_reply_token())

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
