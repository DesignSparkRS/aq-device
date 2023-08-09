import json
import os
import calendar
import requests
from DesignSpark.ESDK import AppLogger
from datetime import datetime
from urllib.parse import urlparse, quote_plus

class LokiHandler:
    def __init__(self, path, debug=False, loggingLevel='full'):
        self.dataDirectory = path
        self.logger = AppLogger.getLogger(__name__, debug, loggingLevel)

    def WriteLogFile(self, data, timestamp):
        try:
            os.makedirs(self.dataDirectory, exist_ok=True)
            builtpath = self.dataDirectory + str(timestamp) + ".json"
            with open(builtpath, "w") as fh:
                fh.write(json.dumps(data))
            self.logger.debug("Written file {}".format(builtpath))
        except Exception as e:
            self.logger.error("Could not write timestamp data file for Loki upload, reason {}".format(str(e)))

    def dt2ts(self, dt):
        """Converts a datetime object to UTC timestamp
        naive datetime will be considered UTC.
        """
        return calendar.timegm(dt.utctimetuple())

    def UploadLogFiles(self, instance, key, url='https://logs-prod-eu-west-0.grafana.net/loki/api/v1/push'):
        """ Uploads log files found in the specified path to the Loki API endpoint """
        totaluploaded = 0
        totalfailed = 0

        for filename in os.scandir(self.dataDirectory):
            if filename.is_file():
                self.logger.debug("Attempting to upload {}".format(filename))

                # Filenames are timestamp.json, strip extension and then store for later use
                ts = filename.name.strip('.json')

                with open(filename, "r") as fh:
                    datapoint = json.loads(fh.read())

                datastruct = {
                    "streams": [{
                        "stream": {},
                        "values": [],
                    }]
                }

                # Stash away labels to be added to all data points
                if 'friendlyname' in datapoint:
                    datastruct['streams'][0]['stream']['friendlyname'] = datapoint.pop('friendlyname')
                if 'hardwareId' in datapoint:
                    datastruct['streams'][0]['stream']['hwid'] = datapoint.pop('hardwareId')
                if 'location' in datapoint:
                    datastruct['streams'][0]['stream']['location'] = datapoint.pop('location')
                if 'project' in datapoint:
                    datastruct['streams'][0]['stream']['project'] = datapoint.pop('project')
                if 'geohash' in datapoint:
                    geohash = datapoint.pop('geohash', None)

                datastring = ""

                # with labels removed all that should be left is dicts containing sensor data
                for sensor, data in datapoint.items():
                    # remove surplus "sensor" tag, not used due to multiple metrics being posted
                    data.pop('sensor')

                    for metric, value in data.items():
                        datastring += "{}={} ".format(metric, value)

                datastring += "geohash={}".format(geohash)

                datastruct['streams'][0]['values'].append([ts, datastring])

                jsonobject = json.dumps(datastruct)
                self.logger.debug("Built JSON object of {}".format(jsonobject))

                keysanitised = quote_plus(key)
                baseurl = url
                spliturl = urlparse(baseurl)

                # Rebuild URL
                completeurl = "{scheme}://{user}:{password}@{url}{path}".format(scheme=spliturl.scheme, \
                user=instance, \
                password=keysanitised, \
                url=spliturl.netloc, \
                path=spliturl.path)

                headers = {
                    "Content-Type":"application/json"
                }

                response = requests.post(completeurl, headers=headers, data=jsonobject)

                if 200 <= response.status_code <= 299:
                    totaluploaded += 1
                    self.logger.debug("Successfully posted {} to Loki, HTTP {}, response {}, success count {}".format(filename, response.status_code, response.text, totaluploaded))
                    os.remove(filename)
                else:
                    totalfailed += 1
                    self.logger.error("Failed posting {} to Loki, HTTP {}, reason {}, fail count {}"\
                        .format(filename, response.status_code, response.text, totalfailed))

        return {'success':totaluploaded, 'fail':totalfailed}

    def GetFileCount(self):
        count = 0
        for path in os.scandir(self.dataDirectory):
            if path.is_file():
                count += 1
        return {"filecount":count}