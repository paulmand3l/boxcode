###############################################################################
##
##  Copyright 2012 Tavendo GmbH
##
##  Licensed under the Apache License, Version 2.0 (the "License");
##  you may not use this file except in compliance with the License.
##  You may obtain a copy of the License at
##
##        http://www.apache.org/licenses/LICENSE-2.0
##
##  Unless required by applicable law or agreed to in writing, software
##  distributed under the License is distributed on an "AS IS" BASIS,
##  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
##  See the License for the specific language governing permissions and
##  limitations under the License.
##
###############################################################################


###############################################################################
##
##
## EDITED BY PAUL MANDEL, Starting July 4th, 2013
##
##
###############################################################################

import sys

from twisted.python import log
from twisted.internet import reactor
from twisted.web.server import Site
from twisted.web.static import File

from autobahn.websocket import listenWS
from autobahn.wamp import exportRpc, WampServerFactory, WampServerProtocol

from Phidgets.PhidgetException import PhidgetException
from Phidgets.Devices.Servo import Servo, ServoTypes


ATTACH = "http://mand3l.com/device/attach"
DETACH = "http://mand3l.com/device/detach"
UPDATE = "http://mand3l.com/device/update"


class WebDevice:
    def __init__(self, Phidget, protocol):
        self.dev = Phidget()
        self.dev.openPhidget()
        self.protocol = protocol

        self.setupHandlers()

    def setupHandlers(self):
        print "Setting up attach and detach handlers"
        self.dev.setOnAttachHandler(self.onAttach)
        self.dev.setOnDetachHandler(self.onDetach)

    def onAttach(self, e):
        print "Device", self.dev.getSerialNum(), "attached."
        self.dev.setPosition(0, 0)
        self.protocol.dispatch(ATTACH, {
            'id': self.dev.getSerialNum(),
            'name': self.dev.getDeviceName(),
        })

    def onDetach(self, e):
        print "Device", self.dev.getSerialNum(), "detached."
        self.protocol.dispatch(DETACH, {
            'id': self.dev.getSerialNum(),
            'name': self.dev.getDeviceName(),
        })


class WebServo(WebDevice):
    def __init__(self, protocol):
        WebDevice.__init__(self, Servo, protocol)

    def onAttach(self, e):
        WebDevice.onAttach(self, e)

        self.dev.setServoParameters(0, 600, 2000, 120)
        self.dev.setPosition(0, (self.dev.getPositionMax(0) - self.dev.getPositionMin(0)) / 2)

    @exportRpc
    def setPosition(self, index=0, position=0):
        print 'Set %s to %s.' % (self.dev, position)
        self.dev.setPosition(index, position)


class DeviceGraph:
    def __init__(self, protocol):
        self.protocol = protocol
        self.devices = []
        self.links = []

        self.createServo()

        for d in self.devices:
            self.protocol.registerForRpc(d, 'http://mand3l.com/devices/%s#' % d.__class__.__name__.lower())

    def createServo(self):
        self.devices.append(WebServo(self.protocol))

    @exportRpc
    def link(self, dev1_id, dev2_id):
        log.msg('Link %s to %s.' % (dev1_id, dev2_id))
        self.links.append([dev1_id, dev2_id])
        #TODO


class DeviceStatusProtocol(WampServerProtocol):
    def onSessionOpen(self):
        self.registerDeviceChannels()
        self.registerDeviceGraph()

    def registerDeviceChannels(self):
        self.registerForPubSub(ATTACH)
        self.registerForPubSub(DETACH)
        self.registerForPubSub(UPDATE)

    def registerDeviceGraph(self):
        self.deviceGraph = DeviceGraph(self)
        self.registerForRpc(self.deviceGraph, 'http://mand3l.com/devices#')


if __name__ == '__main__':

    log.startLogging(sys.stdout)
    debug = len(sys.argv) > 1 and sys.argv[1] == 'debug'

    factory = WampServerFactory("ws://0.0.0.0:9000", debugWamp=debug)
    factory.protocol = DeviceStatusProtocol
    factory.setProtocolOptions(allowHixie76=True)
    listenWS(factory)

    webdir = File("site")
    web = Site(webdir)
    reactor.listenTCP(8080, web)

    reactor.run()
