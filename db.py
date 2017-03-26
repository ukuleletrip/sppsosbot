#! /usr/bin/env python
# -*- coding:utf-8 -*-
from google.appengine.ext import ndb

class Alert(ndb.Model):
    IF_GE = 1
    IF_GT = 2
    IF_LE = 3
    IF_LT = 4
    STAT_OFF = 0
    STAT_ON = 1
    STAT_BLANK = 2
    
    version = ndb.IntegerProperty(required=True, default=1)
    sensor_name = ndb.StringProperty(required=True)
    value = ndb.FloatProperty(required=True)
    alert_type = ndb.IntegerProperty(required=True)
    status = ndb.IntegerProperty(required=True, default=STAT_OFF)
    hyst = ndb.FloatProperty()

    @staticmethod
    def get_key(user_id):
        return ndb.Key(Alert, user_id)


