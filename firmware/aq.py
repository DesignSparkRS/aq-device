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
    debugEnabled = getDebugConfig()

    global mainboard
    mainboard = MAIN.ModMAIN(debug=debugEnabled, configFile=configFile)
    
    global logger
    logger = AppLogger.getLogger(__name__, debugEnabled)
    logger.info("Started main thread")

    hwid = mainboard.getSerialNumber()
    if hwid != -1:
        sensorData.update(hwid)

    global mqtt
    mqtt = MQTT.MQTT(debug=debugEnabled, configDict=mainboard.getMqttConfig(), hwid=hwid['hardwareId'])

    mainboard.createModules()

    logger.debug("Starting sensor update thread")
    sensorsUpdateThreadHandle = threading.Thread(target=sensorsUpdateThread, args=(sensorData, ), daemon=True)
    sensorsUpdateThreadHandle.name = "sensorsUpdateThread"
    sensorsUpdateThreadHandle.start()

    logger.debug("Starting MQTT update thread")
    mqttUpdateThreadHandle = threading.Thread(target=mqttUpdateThread, args=(sensorData, ), daemon=True)
    mqttUpdateThreadHandle.name = "mqttUpdateThread"
    mqttUpdateThreadHandle.start()

    if mainboard.getCsvEnabled():
        logger.debug("Starting CSV update thread")
        csvUpdateThreadHandle = threading.Thread(target=csvUpdateThread, args=(debugEnabled, sensorData, hwid, ), daemon=True)
        csvUpdateThreadHandle.name = "csvUpdateThread"
        csvUpdateThreadHandle.start()

    prometheusThreads = list()
    prometheusConfig = mainboard.getPrometheusConfig()
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
    localConfig.update({'friendlyname': mainboard.getFriendlyName()})
    if int(localConfig['interval']) < 300:
        localConfig['interval'] = 300

    writer = PrometheusWriter.PrometheusWriter(configDict=localConfig, debug=debugEnabled, hwid=hwid)
    logger.debug("Update interval {}s".format(localConfig['interval']))
    while True:
        writer.writeData(sensorData)
        time.sleep(localConfig['interval'])

def csvUpdateThread(debugEnabled, sensorData, hwid):
    logger.debug("Started CSV update thread")
    csv = CsvWriter.CsvWriter(debug=debugEnabled, friendlyName=mainboard.getFriendlyName(), hwid=hwid['hardwareId'])
    while True:
        csv.addRow(sensorData)
        time.sleep(CSV_UPDATE_INTERVAL)

def getDebugConfig():
    """ Open configuration file to read debug information, then close """
    with open(configFile) as fh:
        configData = toml.loads(fh.read())

    return configData['ESDK']['debug']

if __name__ == "__main__":
    main()