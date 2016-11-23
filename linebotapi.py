#! /usr/bin/env python
# -*- coding:utf-8 -*-
#

from google.appengine.api import urlfetch
import logging
import hmac, hashlib, base64
import json

def is_valid_signature(secret, signature, body):
    sig = base64.b64encode(hmac.new(secret,
                                    body,
                                    hashlib.sha256).digest())
    return sig == signature

class WebhookRequest(object):
    def __init__(self, req_body):
        params = json.loads(req_body)
        self.recv_msg = params['events'][0]

    def is_text_message(self):
        return self.recv_msg['type'] == 'message' and \
            self.recv_msg['message']['type'] == 'text'

    def get_message(self):
        return self.recv_msg['message']['text']

    def get_reply_token(self):
        return self.recv_msg['replyToken']


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

        
