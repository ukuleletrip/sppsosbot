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
from google.appengine.api import memcache
from db import Alert
import re
import unicodedata

tz_jst = JST()
tz_utc = UTC()

SOSNAME = 'NagoyaU-Farm'
FSNAME = 'WeatherStation-LUFFT'
BLANK_ALERT_MIN = 30

def parse_alert_setting(user_id, msg):
    mo = re.match(ur'(\S+)が([0-9.]+).*(以上|以下|大きく|小さく|高く|低く|越え|超え).*(知らせて|教えて)',
                  unicodedata.normalize('NFKC', msg))
    if mo:
        sensor_name = SOSAPI.get_sensor_name(mo.group(1))
        if sensor_name:
            cond = mo.group(3)
            if cond == u'以上':
                at = Alert.IF_GE
            elif cond == u'以下':
                at = Alert.IF_LE
            elif cond == u'大きく' or cond == u'高く' or cond == u'超え' or cond == u'越え':
                at = Alert.IF_GT
            elif cond == u'小さく' or cond == u'低く':
                at = Alert.IF_LT

            alert = Alert.get_key(user_id).get()
            if alert is None:
                alert = Alert(id=user_id)
                
            alert.sensor_name = sensor_name
            alert.value = float(mo.group(2))
            alert.alert_type = at
            alert.status = Alert.STAT_OFF
            alert.put()

            return True

    return False


def usage_msg():
    return u'Please see our help page, http://sppsosbot.appspot.com/help'
    

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

                if parse_alert_setting(recv_req.get_user_id(), recv_msg):
                    line_bot_api.reply_message(u'Alert was set.',
                                               recv_req.get_reply_token())
                else:
                    sensor_name = SOSAPI.get_sensor_name(recv_msg)
                    if sensor_name:
                        # at first, check cache
                        value = memcache.get(sensor_name)
                        if value:
                            logging.debug('read from memcache')
                        else:
                            value = sos_api.get_last_sensor_value(SOSNAME, FSNAME,
                                                                  sensor_name)
                            if value:
                                memcache.add(sensor_name, value)

                        if value:
                            now = datetime.now()
                            td = now - value['datetime']
                            td_min = (td.seconds + td.days*24*3600)/60
                            before_str = ' (%d min before)' % (td_min) if td_min > 1 else ''
                            line_bot_api.reply_message('%.1f %s%s' % (value['value'],
                                                                      value['unit'],
                                                                      before_str),
                                                       recv_req.get_reply_token())
                    else:
                        # wrong sensor name or help
                        line_bot_api.reply_message(usage_msg(), recv_req.get_reply_token())

            elif recv_req.is_follow():
                welcome_msg = u'Thank you for adding me to your friends !!!\n Please see our help page, http://sppsosbot.appspot.com/help \n Enjoy!!!'
                line_bot_api.reply_message(welcome_msg,
                                           recv_req.get_reply_token())

        return self.response.write(json.dumps({}))


class PollHandler(webapp2.RequestHandler):
    def get(self):
        sos_api = SOSAPI(APP_KEYS['SOS']['token'], APP_KEYS['SOS']['url'])
        line_bot_api = LineBotAPI(APP_KEYS['line']['token'])
        values = sos_api.get_last_sensor_value(SOSNAME, FSNAME,
                                               SOSAPI.get_all_sensor_name())
        if values:
            for value in values:
                # check blank
                now = datetime.now()
                td = now - value['datetime']
                td_min = (td.seconds + td.days*24*3600)/60
                if td_min > BLANK_ALERT_MIN:
                    query = Alert.query(Alert.sensor_name == value['name'])
                    alerts_to_notice = query.fetch()
                    for alert in alerts_to_notice:
                        logging.debug(alert.key.id())
                        if alert.status != Alert.STAT_BLANK:
                            line_bot_api.send_message(u'%s: %d分間途絶しています' % \
                                                   (SOSAPI.get_sensor_readable_name(value['name']),
                                                       td_min),
                                                      alert.key.id())
                            alert.status = Alert.STAT_BLANK
                            alert.put()
                    continue

                query = Alert.query(Alert.sensor_name == value['name'],
                                    Alert.status == Alert.STAT_BLANK)
                alerts_to_reset = query.fetch()
                for alert in alerts_to_reset:
                    alert.status = Alert.STAT_OFF
                    alert.put()
                
                prev_value = memcache.get(value['name'])
                if prev_value and prev_value['value'] != value['value']:
                    # check alert
                    query = Alert.query(Alert.sensor_name == value['name'],
                                        Alert.value >= min(prev_value['value'], value['value']),
                                        Alert.value <= max(prev_value['value'], value['value']))
                    alerts_to_check = query.fetch()
                    for alert in alerts_to_check:
                        if prev_value['value'] > value['value']:
                            # down
                            if alert.alert_type == Alert.IF_LE:
                                if prev_value['value'] > alert.value and \
                                   value['value'] <= alert.value:
                                    alert.status = Alert.STAT_ON
                            elif alert.alert_type == Alert.IF_LT:
                                if prev_value['value'] >= alert.value and \
                                   value['value'] < alert.value:
                                    alert.status = Alert.STAT_ON
                            elif alert.alert_type == Alert.IF_GE:
                                if prev_value['value'] >= alert.value and \
                                   value['value'] < alert.value:
                                    alert.status = Alert.STAT_OFF
                            elif alert.alert_type == Alert.IF_GT:
                                if prev_value['value'] > alert.value and \
                                   value['value'] <= alert.value:
                                    alert.status = Alert.STAT_OFF


                memcache.set(value['name'], value)


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
