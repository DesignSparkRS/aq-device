# Copyright (c) 2021 RS Components Ltd
# SPDX-License-Identifier: MIT License

'''
MQTT helper class
'''

from DesignSpark.ESDK import AppLogger
from paho.mqtt import client

class MQTT:
	def __init__(self, configDict, debug=False, hwid=0):
		self.logger = AppLogger.getLogger(__name__, debug)
		self.configDict = configDict
		self.hardwareId = hwid

		self.mqttClient = client.Client(str(self.hardwareId))
		self.mqttClient.username_pw_set(self.configDict['username'], self.configDict['password'])
		self.mqttClient.on_connect = self.__onConnect
		try:
			self.mqttClient.connect(self.configDict['broker'], 1883)
		except Exception as e:
			raise e

	def __onConnect(self, client, userData, flags, rc):
		if rc == 0:
			self.logger.info("Connected to MQTT broker")
		else:
			self.logger.error("Failed to connect to MQTT broker, response code {}".format(rc))

	def publishMessage(self, message):
		try:
			topic = "{topic}/{hwid}".format(topic=self.configDict['basetopic'], hwid=str(self.hardwareId))
			result = self.mqttClient.publish(topic, message)
			if result[0] == 0:
				self.logger.debug("Published MQTT message to topic {}".format(topic))
			else:
				self.logger.error("Failed to publish MQTT message")
		except Exception as e:
			raise e
