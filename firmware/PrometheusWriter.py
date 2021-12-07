# Copyright (c) 2021 RS Components Ltd
# SPDX-License-Identifier: MIT License

'''
Prometheus writer helper class
'''

from DesignSpark.ESDK import AppLogger
import requests
import snappy
import prometheus_pb2
#from prometheus_pb2 import TimeSeries, Label, Labels, Sample, WriteRequest
from datetime import datetime
import calendar
import copy

class PrometheusWriter:
    def __init__(self, configDict, debug=False, hwid=0):
        self.logger = AppLogger.getLogger(__name__, debug)
        self.configDict = configDict
        self.hardwareId = hwid
        self.friendlyName = configDict["friendlyname"]

    def __dt2ts(self, dt):
        """Converts a datetime object to UTC timestamp
        naive datetime will be considered UTC.
        """
        return calendar.timegm(dt.utctimetuple())

    def writeData(self, sensorData):
        """ Writes Prometheus data to a specified endpoint """
        # Deep copy the dictionary as it's nested, and we need to pop bits out without affecting other running threads
        sensorDataArray = copy.deepcopy(sensorData)
        try:
            # Strip other keys so all we're left with is sensor data to iterate over
            location = sensorDataArray.pop("geohash", None)
            hwid = sensorDataArray.pop("hardwareId", None)

            # Perform check to ensure sensor data exists in dict
            if sensorDataArray:
                writeRequest = prometheus_pb2.WriteRequest()
                for sensor, sd in sensorDataArray.items():
                    self.logger.debug("PROM sensorData sensor {} dict {}".format(sensor, sd))
                    # Remove sensor type from rest of metrics
                    sensorType = sd.pop("sensor", None)

                    for metric, value in sd.items():
                        metric = metric.replace('.', '_')
                        series = writeRequest.timeseries.add()
                        self.logger.debug("Metric {}, value {}".format(metric, value))

                        # Name label is always required
                        label = series.labels.add()
                        label.name = "__name__"
                        label.value = metric

                        # Add location
                        label = series.labels.add()
                        label.name = "geohash"
                        label.value = location

                        # Add friendly name
                        label = series.labels.add()
                        label.name = "friendlyname"
                        label.value = self.friendlyName

                        # Add hardware ID
                        label = series.labels.add()
                        label.name = "hwid"
                        label.value = self.hardwareId

                        # Add sensor type
                        label = series.labels.add()
                        label.name = "sensor"
                        label.value = sensorType

                        # Add metric value
                        sample = series.samples.add()
                        sample.value = value
                        sample.timestamp = self.__dt2ts(datetime.utcnow()) * 1000

                uncompressed = writeRequest.SerializeToString()
                compressed = snappy.compress(uncompressed)

                username = self.configDict["username"]
                password = self.configDict["password"]
                baseUrl = self.configDict["url"]
                url = "https://{user}:{password}@{url}".format(user=username, password=password, url=baseUrl)
                headers = {
                    "Content-Encoding": "snappy",
                    "Content-Type": "application/x-protobuf",
                    "X-Prometheus-Remote-Write-Version": "0.1.0",
                    "User-Agent": "metrics-worker"
                }

                try:
                    response = requests.post(url, headers=headers, data=compressed)
                    self.logger.debug("POSTed Prometheus data, response code {}".format(response.status_code))
                    if response.status_code != 200:
                        self.logger.error("Error posting Prometheus data, reponse {}".format(response.text))
                except Exception as e:
                    self.logger.error("Could not post Prometheus data, reason {}".format(e))
            
        except Exception as e:
            self.logger.error("Could not format data, reason {}".format(e))