#!/usr/bin/env python
# -*- coding:utf-8 -*-
from datetime import datetime, tzinfo, timedelta

class JST(tzinfo):
    def utcoffset(self, dt):
        return timedelta(hours=9)
    def dst(self, dt): 
        return timedelta(0)
    def tzname(self, dt):
        return 'JST'

class UTC(tzinfo):
    def utcoffset(self, dt):
        return timedelta(0)
    def dst(self, dt): 
        return timedelta(0)
    def tzname(self, dt):
        return 'UTC'

def jst_to_utc(dt):
    return dt.replace(tzinfo=JST()).astimezone(UTC()).replace(tzinfo=None)
