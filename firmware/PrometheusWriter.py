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
from urllib.parse import urlparse
import calendar
import copy

class PrometheusWriter:
    def __init__(self, configDict, debug=False, hwid=0, loggingLevel='full', additionalLabels={}, remoteWriteTimestamps=None):
        self.logger = AppLogger.getLogger(__name__, debug, loggingLevel)
        self.configDict = configDict
        self.hardwareId = hwid
        self.friendlyName = configDict["friendlyname"]
        self.remoteWriteTimestamps = remoteWriteTimestamps

        # Add additional Prometheus labels from dictionary, if dictionary is not empty
        if additionalLabels:
            if "location" in additionalLabels:
                self.locationLabel = additionalLabels["location"]

            if "project" in additionalLabels:
                self.projectLabel = additionalLabels["project"]

            if "tag" in additionalLabels:
                self.tagLabel = additionalLabels["tag"]

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

                        # Attempt to add additional labels if they exist
                        try:
                            label = series.labels.add()
                            label.name = "location"
                            label.value = self.locationLabel
                        except AttributeError:
                            # self.locationLabel doesn't exist, don't add to Prometheus
                            pass

                        try:
                            label = series.labels.add()
                            label.name = "project"
                            label.value = self.projectLabel
                        except AttributeError:
                            # self.projectLabel doesn't exist, don't add to Prometheus
                            pass

                        try:
                            label = series.labels.add()
                            label.name = "tag"
                            label.value = self.tagLabel
                        except AttributeError:
                            # self.tagLabel doesn't exist, don't add to Prometheus
                            pass

                        # Add metric value
                        sample = series.samples.add()
                        sample.value = value
                        sample.timestamp = self.__dt2ts(datetime.utcnow()) * 1000

                uncompressed = writeRequest.SerializeToString()
                compressed = snappy.compress(uncompressed)

                username = self.configDict["instance"]
                password = self.configDict["key"]
                baseUrl = self.configDict["url"]
                splitUrl = urlparse(baseUrl)

                # Rebuild URL
                url = "{scheme}://{user}:{password}@{url}{path}".format(scheme=splitUrl.scheme, \
                    user=username, \
                    password=password, \
                    url=splitUrl.netloc, \
                    path=splitUrl.path)

                headers = {
                    "Content-Encoding": "snappy",
                    "Content-Type": "application/x-protobuf",
                    "X-Prometheus-Remote-Write-Version": "0.1.0",
                    "User-Agent": "metrics-worker"
                }

                try:
                    response = requests.post(url, headers=headers, data=compressed)
                    # Check for valid success code (not using response.ok as this includes 2xx and 3xx codes)
                    if 200 <= response.status_code <= 299:
                        self.logger.debug("Successfully posted Prometheus data, reponse {}".format(response.text))
                        if self.remoteWriteTimestamps:
                            self.remoteWriteTimestamps['remoteWriteSuccess'] = int(datetime.now().timestamp())
                    else:
                        self.logger.error("Failed posting Prometheus data! Status code {}, response {}".format(response.status_code, response.text))
                        if self.remoteWriteTimestamps:
                            self.remoteWriteTimestamps['remoteWriteFail'] = int(datetime.now().timestamp())
                except Exception as e:
                    self.logger.error("Could not post Prometheus data, reason {}".format(e))
            
        except Exception as e:
            self.logger.error("Could not format data, reason {}".format(e))