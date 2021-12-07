# Copyright (c) 2021 RS Components Ltd
# SPDX-License-Identifier: MIT License

'''
CSV writer helper class
'''

from DesignSpark.ESDK import AppLogger
import csv
import copy
from datetime import datetime

class CsvWriter:
    def __init__(self, friendlyName='', debug=False, hwid=0):
        self.logger = AppLogger.getLogger(__name__, debug)
        self.hardwareId = hwid
        self.friendlyName = friendlyName
        self.csvFilename = "/aq/data/{fn}_{hwid}_{ts}.csv".format(fn=self.friendlyName, hwid=self.hardwareId, ts=datetime.utcnow().strftime("%Y_%m_%d-%H_%M_%S"))

        # Should more sensors be added, this should be updated to reflect available values
        self.csvColumns = ['timestamp', 'temperature', 'humidity', 'vocIndex', 'co2', 'pm1.0', 'pm2.5', 'pm4.0', 'pm10']

        with open(self.csvFilename, 'w') as fh:
            csvWriter = csv.DictWriter(fh, fieldnames=self.csvColumns)
            csvWriter.writeheader()

    def addRow(self, sensorData):
        sensorDataArray = copy.deepcopy(sensorData)
        try:
            # Strip other keys so all we're left with is sensor data to iterate over
            location = sensorDataArray.pop("geohash", None)
            hwid = sensorDataArray.pop("hardwareId", None)

            csvSensorDataArray = {'timestamp': int(datetime.utcnow().timestamp())}

            for sensorType, sd in sensorDataArray.items():
                sd.pop("sensor", None) # Remove sensor type from data array
                csvSensorDataArray.update(sd)

            self.logger.debug("CSV data dict {}".format(csvSensorDataArray))

            with open(self.csvFilename, 'a') as fh:
                csvWriter = csv.DictWriter(fh, fieldnames=self.csvColumns)
                csvWriter.writerow(csvSensorDataArray)

        except Exception as e:
            self.logger.error("Could not write CSV data, reason {}".format(e))