# Copyright (c) 2022 RS Components Ltd
# SPDX-License-Identifier: MIT License

'''
Web server helper class
'''

from twisted.web.server import Site
from twisted.web.static import File
from twisted.internet import reactor
from twisted.internet import endpoints
from DesignSpark.ESDK import AppLogger

class WebServer:
	def __init__(self, debug=False, loggingLevel='full', port=8080):
		self.logger = AppLogger.getLogger(__name__, debug, loggingLevel)
		self.resource = File('../dashboard')
		self.factory = Site(self.resource)
		self.endpoint = endpoints.TCP4ServerEndpoint(reactor, port)

	def run(self):
		self.logger.debug("Starting web server")
		self.endpoint.listen(self.factory)
		reactor.run(installSignalHandlers=False)