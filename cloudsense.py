#! /usr/bin/env python
# -*- coding:utf-8 -*-
#

from google.appengine.api import urlfetch, urlfetch_errors
import urllib
import logging
import json
import HTMLParser
from datetime import datetime, tzinfo
from tzimpl import jst_to_utc

class CloudSenseAPI(object):
    sensor_names = {
        'air_temperature' : [
            u'気温',
            u'温度',
            'temperature',
            'temp'
        ],
        'relative_humidity' : [
            u'湿度',
            'humidity',
            'hum'
        ],
        'air_pressure' : [
            u'気圧',
            'pressure'
        ],
        'wind_speed' : [
            u'風速',
            'wind speed'
        ],
        '1min_precipitation' : [
            u'降雨',
            u'降水',
            'precipitation'
        ],
        'solar_irradiance' : [
            u'日射',
            'solar',
            'irradiance',
            'light'
        ]
    }

    def __init__(self, token, url):
        self.token = token
        self.url = url

    @staticmethod
    def get_sensor_name(name):
        for sensor_name, alt_names in CloudSenseAPI.sensor_names.items():
            if name == sensor_name:
                return sensor_name
            for alt_name in alt_names:
                if name.find(alt_name) >= 0:
                    return sensor_name
        return None

    @staticmethod
    def get_all_sensor_name():
        sensors = []
        for sensor_name in CloudSenseAPI.sensor_names:
            sensors.append(sensor_name)
        return sensors

    @staticmethod
    def get_sensor_readable_name(sensor_name):
        names = CloudSenseAPI.sensor_names.get(sensor_name)
        if names:
            return names[0]
        return ''

    @staticmethod
    def _measurement_to_valueobject(m):
        return { 'name' : m['observedProperty'],
                 'datetime' : jst_to_utc(datetime.strptime(m['Time']['content'],
                                                           '%Y-%m-%d %H:%M:%S')),
                 'value' : m['Result']['content'],
                 'unit' : HTMLParser.HTMLParser().unescape(m['Result']['uom']) }

    def get_last_sensor_value(self, sosname, fsname, sensor):
        if type(sensor) == list:
            sensor = ','.join(sensor)

        params = { 'Key' : self.token,
                   'Cmd' : 'GET-SENSOR-OBSERVATION-LASTN',
                   'SOSName' : sosname,
                   'FSName' : fsname,
                   'Sensors' : sensor,
                   'NRecords' : 1,
                   'OutputType' : 'json'
        }

        for i in range(5):
            try:
                result = urlfetch.fetch(url = self.url + urllib.urlencode(params),
                                        deadline = 30)
                logging.debug(result.content)
                break
            except urlfetch_errors.DeadlineExceededError:
                # retry
                logging.debug('retry %d' % (i))
                continue
        else:
            return None

        measurement = json.loads(result.content)['BASEELEMENT']['Observations']['Measurement']
        if type(measurement) == list:
            rv = []
            for m in measurement:
                rv.append(self._measurement_to_valueobject(m))
            return rv
        else:
            return self._measurement_to_valueobject(measurement)
