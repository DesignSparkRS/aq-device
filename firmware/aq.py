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
from DesignSpark.ESDK import MAIN, THV, CO2, PM2, AppLogger
import PrometheusWriter, CsvWriter, MQTT

configFile='/boot/aq/aq.toml'
debugEnabled = False

sensorData = {}

WEBSOCKET_UPDATE_INTERVAL = 5
CSV_UPDATE_INTERVAL = 30

async def websocketPush(websocket, path):
    logger.debug("Websocket connection from {}".format(websocket.remote_address))
    while True:
        await websocket.send(json.dumps(sensorData, ensure_ascii=False))
        await asyncio.sleep(WEBSOCKET_UPDATE_INTERVAL)

def main():
    global configData
    configData = getConfig()
    debugEnabled = configData['ESDK']['debug']

    global mainboard
    mainboard = MAIN.ModMAIN(debug=debugEnabled, config=configData)
    
    global logger
    logger = AppLogger.getLogger(__name__, debugEnabled)
    logger.info("Started main thread")

    hwid = mainboard.getSerialNumber()
    if hwid != -1:
        sensorData.update(hwid)

    mainboard.createModules()

    logger.debug("Starting sensor update thread")
    sensorsUpdateThreadHandle = threading.Thread(target=sensorsUpdateThread, args=(sensorData, ), daemon=True)
    sensorsUpdateThreadHandle.name = "sensorsUpdateThread"
    sensorsUpdateThreadHandle.start()

    global mqtt
    mqttConfig = getMqttConfig()

    if mqttConfig is not None:
        mqtt = MQTT.MQTT(debug=debugEnabled, configDict=getMqttConfig(), hwid=hwid['hardwareId'])
        logger.debug("Starting MQTT update thread")
        mqttUpdateThreadHandle = threading.Thread(target=mqttUpdateThread, args=(sensorData, ), daemon=True)
        mqttUpdateThreadHandle.name = "mqttUpdateThread"
        mqttUpdateThreadHandle.start()

    if getCsvEnabled():
        logger.debug("Starting CSV update thread")
        csvUpdateThreadHandle = threading.Thread(target=csvUpdateThread, args=(debugEnabled, sensorData, hwid, ), daemon=True)
        csvUpdateThreadHandle.name = "csvUpdateThread"
        csvUpdateThreadHandle.start()

    prometheusConfig = getPrometheusConfig()

    if prometheusConfig is not None:
        prometheusThreads = list()
        prometheusConfig.pop('friendlyname', None)

        for name, config in prometheusConfig.items():
            logger.debug("Starting Prometheus update thread for config {}".format(name))
            prometheusUpdateThreadHandle = threading.Thread(target=prometheusUpdateThread, args=(config, debugEnabled, sensorData, hwid['hardwareId']), daemon=True)
            prometheusUpdateThreadHandle.name = "prometheusUpdateThread_{}".format(name)
            prometheusThreads.append(prometheusUpdateThreadHandle)
            prometheusUpdateThreadHandle.start()

    logger.debug("Starting asyncio websocket")
    asyncio.run(startWebsocket())

    while True:
        pass

async def startWebsocket():
    logger.debug("Started websocket")
    async with websockets.serve(websocketPush, "0.0.0.0", 8765):
        await asyncio.Future()  # run forever

def sensorsUpdateThread(sensorDataHandle):
    logger.debug("Started sensor update thread")
    while True:
        sensorDataHandle.update(mainboard.readAllModules())
        sensorDataHandle.update(mainboard.getLocation())
        time.sleep(1)

def mqttUpdateThread(sensorData):
    logger.debug("Started MQTT thread")
    while True:
        mqtt.publishMessage(json.dumps(sensorData))
        time.sleep(WEBSOCKET_UPDATE_INTERVAL)

def prometheusUpdateThread(config, debugEnabled, sensorData, hwid):
    logger.debug("Started Prometheus update thread")

    localConfig = config
    localConfig.update({'friendlyname': getFriendlyName()})
    if int(localConfig['interval']) < 300:
        localConfig['interval'] = 300

    writer = PrometheusWriter.PrometheusWriter(configDict=localConfig, debug=debugEnabled, hwid=hwid)
    logger.debug("Update interval {}s".format(localConfig['interval']))
    while True:
        writer.writeData(sensorData)
        time.sleep(localConfig['interval'])

def csvUpdateThread(debugEnabled, sensorData, hwid):
    logger.debug("Started CSV update thread")
    csv = CsvWriter.CsvWriter(debug=debugEnabled, friendlyName=getFriendlyName(), hwid=hwid['hardwareId'])
    while True:
        csv.addRow(sensorData)
        time.sleep(CSV_UPDATE_INTERVAL)

def getConfig():
    """ Open configuration file to read config information, then close """
    with open(configFile) as fh:
        return toml.loads(fh.read())

def getMqttConfig():
    """ Return a dictionary containing MQTT config """
    if 'mqtt' in configData:
        return configData['mqtt']
    else:
        return None

def getPrometheusConfig():
    """ Return a dictionary containing Prometheus config, and friendly name """
    configDict = {}
    if 'prometheus' in configData:
        configDict.update(configData['prometheus'])
        configDict.update({"friendlyname": configData["ESDK"]["friendlyname"]})
        return(configDict)
    else:
        return None

def getFriendlyName():
    """ Return the string of the device friendly name """
    return configData['ESDK']['friendlyname']

def getCsvEnabled():
    """ Return CSV enabled value """
    if configData['local']['csv'] is not None:
        return configData['local']['csv']
    else:
        return False

if __name__ == "__main__":
    main()