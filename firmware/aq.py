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
import sys
import RPi.GPIO as GPIO
from datetime import datetime
from DesignSpark.ESDK import MAIN, THV, CO2, PM2, NO2, NRD, FDH, AppLogger
import PrometheusWriter, CsvWriter, MQTT, WebServer, LokiHandler

configFile='/boot/aq/aq.toml'
lokiDataDirectory='/aq/data/offline/'
debugEnabled = False

loggingButton = 19

sensorData = {}
debugData = {}
csvLoggingEnabledState = False

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

async def controlWebsocket(websocket, path):
    logger.debug("Websocket connection from {}".format(websocket.remote_address))
    async for message in websocket:
        logger.debug("Control websocket message {}".format(message))
        message = json.loads(message)
        if 'command' in message:
            if message['command'] == "filecount":
                await websocket.send(json.dumps({"result":lokiLogger.GetFileCount()}))

            if message['command'] == "upload":
                config = getLokiConfig()
                instance = config['instance']
                key = config['key']
                result = lokiLogger.UploadLogFiles(instance, key)
                await websocket.send(json.dumps({"result":result}))

def main():
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(loggingButton, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(loggingButton, GPIO.RISING)

    buttonWatcherThreadHandle = threading.Thread(target=buttonWatcherThread, \
        args=(), \
        daemon=True)
    buttonWatcherThreadHandle.name = "buttonWatcherThread"
    buttonWatcherThreadHandle.start()

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

    global lokiLogger
    lokiLogger = LokiHandler.LokiHandler(lokiDataDirectory, debugEnabled)

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
    time.sleep(1)
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

    global csvLoggingEnabledState
    csvEnabled = getCsvEnabled()
    # CSV thread init
    if csvEnabled:
        logger.debug("Starting CSV update thread")
        csvUpdateThreadHandle = threading.Thread(target=csvUpdateThread, \
            args=(debugEnabled, sensorData, hwid, loggingConfig), \
            daemon=True)
        csvLoggingEnabledState = csvEnabled
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

    logger.debug("Starting web server thread")
    webServerThreadHandle = threading.Thread(target=webServerThread, \
        args=(debugEnabled, loggingConfig), \
        daemon=True)
    webServerThreadHandle.name = "webServerThread"
    webServerThreadHandle.start()

    logger.debug("Starting control websocket thread")
    controlWebsocketThreadHandle = threading.Thread(target=controlWebsocketThread, \
        args=(), \
        daemon=True)
    controlWebsocketThreadHandle.name = "controlWebsocketThread"
    controlWebsocketThreadHandle.start()

    logger.debug("Starting asyncio data websocket")
    asyncio.run(startWebsocket())

    while True:
        pass

async def startWebsocket():
    logger.debug("Started data websocket")
    async with websockets.serve(websocketPush, "0.0.0.0", 8765):
        await asyncio.Future()  # run forever

def controlWebsocketThread():
    logger.debug("Started control websocket thread")
    logger.debug("Starting asyncio control websocket")
    asyncio.run(startControlWebsocket())


async def startControlWebsocket():
    logger.debug("Started control websocket")
    async with websockets.serve(controlWebsocket, "0.0.0.0", 8766):
        await asyncio.Future()  # run forever

def webServerThread(debugEnabled, loggingLevel):
    logger.debug("Started web server thread")
    ws = WebServer.WebServer(debug=debugEnabled, loggingLevel=loggingLevel)
    ws.run()
    logger.debug("Web server should be running")
    while True:
        pass

def buttonWatcherThread():
    global csvLoggingEnabledState
    while True:
        if GPIO.event_detected(loggingButton):
            if csvLoggingEnabledState:
                logger.debug("Stopping CSV logging on user request")
                csvLoggingEnabledState = False
                debugData.update({'csvEnabled': csvLoggingEnabledState})
            elif not csvLoggingEnabledState:
                logger.debug("Starting CSV logging on user request")
                csvLoggingEnabledState = True
                debugData.update({'csvEnabled': csvLoggingEnabledState})

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


    if getOfflineLoggingConfig() == "auto":
        lokiEnabled = True
    else:
        lokiEnabled = False

    while True:
        try:
            writer.writeData(sensorData)
        except Exception as e:
            if lokiEnabled:
                # Add additional data to sensor data dictionary
                sensorDataCopy = copy.deepcopy(sensorData)
                sensorDataCopy.update({'friendlyname': getFriendlyName()})

                if 'project' in configData['ESDK']:
                    sensorDataCopy.update({'project': configData['ESDK']['project']})
                if 'location' in configData['ESDK']:
                    sensorDataCopy.update({'location': configData['ESDK']['location']})
                if 'tag' in configData['ESDK']:
                    sensorDataCopy.update({'tag': configData['ESDK']['tag']})

                # Generate timestamp in nanoseconds (as per Loki documentation)
                ts = lokiLogger.dt2ts(datetime.utcnow()) * 1000000000

                lokiLogger.WriteLogFile(data=sensorDataCopy, timestamp=ts)
            else:
                pass

        time.sleep(localConfig['interval'])

def csvUpdateThread(debugEnabled, sensorData, hwid, loggingLevel):
    logger.debug("Started CSV update thread")
    global csvLoggingEnabledState
    firstRun = True
    csv = None
    while True:
        if csvLoggingEnabledState:
            if firstRun == True:
                logger.info("Starting CSV logging")
                csv = CsvWriter.CsvWriter(debug=debugEnabled, \
                friendlyName=getFriendlyName(), \
                hwid=hwid['hardwareId'], \
                loggingLevel=loggingLevel)
                firstRun = False

            csv.addRow(sensorData)
            time.sleep(CSV_UPDATE_INTERVAL)

        if not csvLoggingEnabledState:
            firstRun = True
            csv = None

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

        if 'loki' in config:
            firstConfigKey = list(config['loki'].keys())[0]
            if 'instance' not in config['loki'][firstConfigKey]:
                config_logger.error("Missing [loki] 'instance' key")
            if 'key' not in config['loki'][firstConfigKey]:
                config_logger.error("Missing [loki] 'key' key")
            if 'url' not in config['loki'][firstConfigKey]:
                config_logger.error("Missing [loki] 'url' key")    



        # Optional config key checking
        if 'NO2' in config:
            if 'sensitivity' not in config['NO2']:
                config_logger.error("Missing [NO2] sensitivity code, must be provided if using NO2 sensor")
        else:
            config_logger.warning("Missing [NO2] configuration section, must be provided if using NO2 sensor!")

        if 'local' not in config:
            config_logger.warning("Optional [local] configuration section not provided")
        else:
            if 'logging' not in config['local']:
                config_logger.error("Missing [local] 'logging' key")
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

def getOfflineLoggingConfig():
    """ Return a string pertaining to Loki logging configuration """
    if 'local' in configData:
        if 'logging' in configData['local']:
            return configData['local']['logging']
    else:
        return "off"

def getLokiConfig():
    if 'loki' in configData:
        firstConfigKey = list(configData['loki'].keys())[0]
        return configData['loki'][firstConfigKey]

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