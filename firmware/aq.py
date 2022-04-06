# Copyright (c) 2021 RS Components Ltd
# SPDX-License-Identifier: MIT License

'''
Python application for logging data from ESDK hardware
'''

import asyncio
import websockets
import json
import time
import threading
import logging
import toml
import subprocess
import copy
import geohash
import re
import shutil
from DesignSpark.ESDK import MAIN, THV, CO2, PM2, AppLogger
import PrometheusWriter, CsvWriter, MQTT

configFile='/boot/aq/aq.toml'
debugEnabled = False

sensorData = {}
debugData = {}

WEBSOCKET_UPDATE_INTERVAL = 5
CSV_UPDATE_INTERVAL = 30
PROMETHEUS_MIN_UPDATE_INTERVAL = 120

async def websocketPush(websocket, path):
    logger.debug("Websocket connection from {}".format(websocket.remote_address))
    while True:
        localData = copy.deepcopy(sensorData)
        localData.update({"debug": debugData})
        await websocket.send(json.dumps(localData, ensure_ascii=False))
        await asyncio.sleep(WEBSOCKET_UPDATE_INTERVAL)

def main():
    global configData
    configData = getConfig()

    # Check for logging level setup, default to full if non-existant configuration
    if 'logging' in configData['ESDK']:
        loggingConfig = configData['ESDK']['logging']
    else:
        loggingConfig = 'full'

    debugEnabled = getDebugConfig()
    global logger
    logger = AppLogger.getLogger(__name__, debugEnabled, loggingConfig)

    global mainboard
    mainboard = MAIN.ModMAIN(debug=debugEnabled, config=configData, \
        loggingLevel=loggingConfig)

    global appGitCommit
    appGitCommit = {"appVersion": getAppCommitHash()}
    debugData.update(appGitCommit)

    global remoteWriteTimestamps
    remoteWriteTimestamps = {'remoteWriteSuccess': 0, 'remoteWriteFail': 0}

    debugData.update({'csvEnabled': getCsvEnabled()})
    debugData.update({'debugEnabled': debugEnabled})

    # Give sensor string a restart
    mainboard.setPower(vcc3=False, vcc5=False)
    mainboard.setBuzzer(freq=20000)
    time.sleep(0.5)
    mainboard.setBuzzer(freq=0)
    mainboard.setPower(vcc3=True, vcc5=True)
    
    logger.info("Started main thread")

    hwid = mainboard.getSerialNumber()
    if hwid != -1:
        sensorData.update(hwid)

    debugData.update(mainboard.getModuleVersion())

    # Give sensors some time to sort themselves out before attempting to read
    time.sleep(0.05)
    mainboard.createModules()
    time.sleep(0.05)

    logger.debug("Starting sensor update thread")
    sensorsUpdateThreadHandle = threading.Thread(target=sensorsUpdateThread, \
        args=(sensorData, ), \
        daemon=True)
    sensorsUpdateThreadHandle.name = "sensorsUpdateThread"
    sensorsUpdateThreadHandle.start()

    global mqtt
    mqttConfig = getMqttConfig()

    # MQTT thread init
    if mqttConfig is not None:
        mqtt = MQTT.MQTT(debug=debugEnabled, \
            configDict=getMqttConfig(), \
            hwid=hwid['hardwareId'], \
            loggingLevel=loggingConfig)

        logger.debug("Starting MQTT update thread")
        mqttUpdateThreadHandle = threading.Thread(target=mqttUpdateThread, \
            args=(sensorData, ), \
            daemon=True)

        mqttUpdateThreadHandle.name = "mqttUpdateThread"
        mqttUpdateThreadHandle.start()


    # CSV thread init
    if getCsvEnabled():
        logger.debug("Starting CSV update thread")
        csvUpdateThreadHandle = threading.Thread(target=csvUpdateThread, \
            args=(debugEnabled, sensorData, hwid, loggingConfig), \
            daemon=True)

        csvUpdateThreadHandle.name = "csvUpdateThread"
        csvUpdateThreadHandle.start()


    # Prometheus threads init
    prometheusConfig = getPrometheusConfig()
    if prometheusConfig is not None:
        prometheusThreads = list()

        # Start thread for each configuration present
        for name, config in prometheusConfig.items():
            logger.debug("Starting Prometheus update thread for config {}".format(name))
            prometheusUpdateThreadHandle = threading.Thread(target=prometheusUpdateThread, \
                args=(config, debugEnabled, sensorData, hwid['hardwareId'], loggingConfig), \
                daemon=True)

            prometheusUpdateThreadHandle.name = "prometheusUpdateThread_{}".format(name)
            prometheusThreads.append(prometheusUpdateThreadHandle)
            prometheusUpdateThreadHandle.start()

        logger.debug("Started Prometheus threads: {}".format(prometheusThreads))

    logger.debug("Starting asyncio websocket")
    asyncio.run(startWebsocket())

    while True:
        # Main thread loop
        pass

async def startWebsocket():
    logger.debug("Started websocket")
    async with websockets.serve(websocketPush, "0.0.0.0", 8765):
        await asyncio.Future()  # run forever

def sensorsUpdateThread(sensorDataHandle):
    logger.debug("Started sensor update thread")
    while True:
        sensorDataHandle.update(mainboard.readAllModules())

        try:
            rawLocation = mainboard.getLocation()
            sensorDataHandle.update({'geohash': geohash.encode(rawLocation['lat'], rawLocation['lon'])})
            debugData.update({'location': {'lat': rawLocation['lat'], 'lon': rawLocation['lon']}})
        except Exception as e:
            pass

        debugData.update({'aqUsed': getAqUsedPercentage()})
        debugData.update(mainboard.getUndervoltageStatus())
        debugData.update(mainboard.getGPSStatus())
        debugData.update({'remoteWriteStats': remoteWriteTimestamps})

        time.sleep(1)

def mqttUpdateThread(sensorData):
    logger.debug("Started MQTT thread")
    while True:
        mqtt.publishMessage(json.dumps(sensorData))
        time.sleep(WEBSOCKET_UPDATE_INTERVAL)

def prometheusUpdateThread(config, debugEnabled, sensorData, hwid, loggingLevel):
    logger.debug("Started Prometheus update thread")

    localConfig = config
    localConfig.update({'friendlyname': getFriendlyName()})

    # Enforce a mininmum logging interval
    if "interval" in localConfig:
        if int(localConfig['interval']) < PROMETHEUS_MIN_UPDATE_INTERVAL:
            logger.warning("Minimum Prometheus logging interval of {}s enforced".format(PROMETHEUS_MIN_UPDATE_INTERVAL))
            localConfig['interval'] = PROMETHEUS_MIN_UPDATE_INTERVAL
    else:
        logger.warning("No Prometheus interval specified, enforcing miniumum of {}s".format(PROMETHEUS_MIN_UPDATE_INTERVAL))
        localConfig['interval'] = PROMETHEUS_MIN_UPDATE_INTERVAL

    writer = PrometheusWriter.PrometheusWriter(configDict=localConfig, \
        debug=debugEnabled, \
        hwid=hwid, \
        loggingLevel=loggingLevel, \
        additionalLabels=configData['ESDK'], \
        remoteWriteTimestamps = remoteWriteTimestamps)

    while True:
        writer.writeData(sensorData)
        time.sleep(localConfig['interval'])

def csvUpdateThread(debugEnabled, sensorData, hwid, loggingLevel):
    logger.debug("Started CSV update thread")
    csv = CsvWriter.CsvWriter(debug=debugEnabled, \
        friendlyName=getFriendlyName(), \
        hwid=hwid['hardwareId'], \
        loggingLevel=loggingLevel)
    while True:
        csv.addRow(sensorData)
        time.sleep(CSV_UPDATE_INTERVAL)

def getDebugConfig():
    """ Return debugging configuration """
    with open(configFile) as fh:
        config = toml.loads(fh.read())
        try:
            return config['ESDK']['debug']
        except Exception as e:
            print("Could not read [ESDK] 'debug' key, defaulting to no debug output")
            return False

def getConfig():
    """ Open configuration file to read config information, then close """

    # Initialise temporary logger for use here
    # Necessary as the AppLogger isn't created yet
    config_logger = logging.getLogger('config_checker')
    config_logger.setLevel(logging.DEBUG)
    sh = logging.StreamHandler()
    logger_formatter = logging.Formatter('%(name)s [%(levelname)s]: %(message)s')
    sh.setFormatter(logger_formatter)
    config_logger.addHandler(sh)

    with open(configFile) as fh:
        config = toml.loads(fh.read())

        # Regex to sanitise some inputs
        string_strip = re.compile("\W+")

        # Mandatory config key checking
        if 'ESDK' in config:
            if 'friendlyname' not in config['ESDK']:
                config_logger.error("Missing [ESDK] 'friendlyname' key!")
            else:
                # Remove anything other than A-Z, a-z, 0-9 and _
                config['ESDK']['friendlyname'] = string_strip.sub('', config['ESDK']['friendlyname'])
            if 'location' not in config['ESDK']:
                config_logger.error("Missing [ESDK] 'location' key!")
            if 'latitude' not in config['ESDK']:
                config_logger.error("Missing [ESDK] 'latitude' key!")
            if 'longitude' not in config['ESDK']:
                config_logger.error("Missing [ESDK] 'longitude' key!")

            # Optional Prometheus label sanitising
            if 'location' in config['ESDK']:
                config['ESDK']['location'] = string_strip.sub('', config['ESDK']['location'])
            if 'project' in config['ESDK']:
                config['ESDK']['project'] = string_strip.sub('', config['ESDK']['project'])
            if 'tag' in config['ESDK']:
                config['ESDK']['tag'] = string_strip.sub('', config['ESDK']['tag'])
        else:
            config_logger.error("Missing [ESDK] configuration section!")

        # Optional config key checking
        if 'local' not in config:
            config_logger.warning("Optional [local] configuration section not provided")
        if 'mqtt' not in config:
            config_logger.warning("Optional [mqtt] configuration section not provided")
        else:
            if 'broker' not in config['mqtt']:
                config_logger.error("Missing [mqtt] 'broker' key!")
            if 'basetopic' not in config['mqtt']:
                config_logger.error("Missing [mqtt] 'basetopic' key!")
            if 'username' not in config['mqtt']:
                config_logger.error("Missing [mqtt] 'username' key! Set to empty string if not needed")
            if 'password' not in config['mqtt']:
                config_logger.error("Missing [mqtt] 'password' key! Set to empty string if not needed")
        if 'prometheus' not in config:
            config_logger.warning("Optional [prometheus] configuration section not provided")
        else:
            # Prometheus enabled, check for configuration value presence
            for config_name, config_section in config['prometheus'].items():
                if 'instance' not in config_section:
                    config_logger.error("Missing [prometheus.{name}] 'instance' key!".format(name=config_name))
                if 'key' not in config_section:
                    config_logger.error("Missing [prometheus.{name}] 'key' key!".format(name=config_name))
                if 'url' not in config_section:
                    config_logger.error("Missing [prometheus.{name}] 'url' key!".format(name=config_name))
                if 'interval' not in config_section:
                    config_logger.warning("Missing [prometheus.{name}] 'interval' key".format(name=config_name))

        return config

def getMqttConfig():
    """ Return a dictionary containing MQTT config """
    if 'mqtt' in configData:
        return configData['mqtt']
    else:
        return None

def getPrometheusConfig():
    """ Return a dictionary containing Prometheus config, and friendly name """
    if 'prometheus' in configData:
        return(configData['prometheus'])
    else:
        return None

def getFriendlyName():
    """ Return the string of the device friendly name """
    if 'friendlyname' in configData['ESDK']:
        return configData['ESDK']['friendlyname']
    else:
        return ""

def getCsvEnabled():
    """ Return CSV enabled value """
    if 'local' in configData:
        if 'csv' in configData['local']:
            return configData['local']['csv']
        else:
            logger.warning("Missing [local] 'csv' key, defaulting to no CSV logging")
            return False
    else:
        return False

def getAppCommitHash() -> str:
    """ Try get application git commit hash """
    # Taken from https://stackoverflow.com/a/21901260
    try:
        return subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).decode('ascii').strip()
    except Exception as e:
        logger.error("Could not determine Git hash! Reason {}".format(e))
        return ""

def getAqUsedPercentage() -> int:
    try:
        aqStats = shutil.disk_usage("/aq")
        aqUsed = round((aqStats.used / aqStats.total) * 100, 1)
        return aqUsed
    except Exception as e:
        logger.error("Could not get /aq free space, reason {}".format(e))
        return 0

if __name__ == "__main__":
    main()