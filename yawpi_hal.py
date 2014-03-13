#=================================================================
# hardware abstraction layer
#=================================================================

# random numbers for sensors when hardware is not present:
import random

# gv - 'global vars' - an empty module, used for storing vars (as attributes),
# that need to be 'global' across threads and between functions and classes:
import gv


class yawpiHAL:
    def check_config(self):  # check hw config
        # for pin collisions/correct WLS settings:
        # XXX
        pass

    def check_gpio(self):  # tests if gpio present, else simulated mode is set
        # gv.hw['WithHW']: If set, runs with pumps and valves and
        # real sensors, if unset, no hardware access is performed. If import
        # GPIO failes it is unset:
        gv.hw['WithHW'] = 1
        try:
            import RPi.GPIO as GPIO  # RPi general purpose input/output library
            self.gpio = GPIO
        # for different python versions different error occurs
            # version 2.7.3: ImportError occurs
            # some other version: RuntimeError occurs
        except (ImportError, RuntimeError):
            gv.hw['WithHW'] = 0

    def init(self):  # initialization of hw and variables
        # general setup
        if gv.hw['WithHW']:
            self.gpio.setmode(self.gpio.BOARD)
            gv.hw['RPiRevision'] = self.gpio.RPI_REVISION
        else:
            gv.hw['RPiRevision'] = 'no hardware mode'
        if gv.hw['WithHW']:
            # port expander:
            from Adafruit_MCP23016 import Adafruit_MCP23016
            self.pe = Adafruit_MCP23016(address=gv.hw['PeAddress'])
            # ad converter:
            # from class_MCP32008 import class_MCP32008
            # self.adc = class_MCP32008(address=gv.hw['PeAddress'])

        # init variables:
        gv.hw['StValveState'] = [0] * gv.hw['StNo']

        # setup hw to default values:
        if gv.hw['WithHW']:
            # setup port expander:
            for x in range(0, 15):              # set all as inputs
                self.pe.config(x, self.pe.INPUT)
            # set pump port as output:
            self.pe.config(gv.hw['PuPin'], self.pe.OUTPUT)
            # set valve ports as output
            for x in gv.hw['StValvePin']:
                self.pe.config(x, self.pe.OUTPUT)
            # setup pumps and valves:
            self.pump_switch(0)                       # switch of pump
            for x in range(0, gv.hw['StNo']):         # switch of valves
                self.valve_switch(x, 0)

    def clean_up(self):  # cleans GPIO
        if gv.hw['WithHW']:
            self.gpio.cleanup()

    def pump_switch(self, state):  # sets pump on or off
        if state == 0:
            # switch off
            gv.hw['PuState'] = 0
            if gv.hw['WithHW']:
                self.pe.output(gv.hw['PuPin'],  0)
        else:
            # switch on
            gv.hw['PuState'] = 1
            if gv.hw['WithHW']:
                self.pe.output(gv.hw['PuPin'],  1)

    def valve_switch(self, index,  state):  # sets valve on or off
        if index < 0 or index > gv.hw['StNo']:
            raise NameError('incorrect valve index')
        if state == 0:
            # switch valve off
            gv.hw['StValveState'][index] = 0
            if gv.hw['WithHW']:
                self.pe.output(gv.hw['StValvePin'][index],  0)
        else:
            # switch valve on
            gv.hw['StValveState'][index] = 1
            if gv.hw['WithHW']:
                self.pe.output(gv.hw['StValvePin'][index],  1)

    def sens_wl_status(self, index):  # returns amount of water in the station
        if gv.hw['WithHW']:
            if gv.hw['StWLSensorType'][index] == 'none':
                # if no sensor consider station always empty:
                return 0
            elif gv.hw['StWLSensorType'][index] == 'min':
                return self.pe.input(gv.hw['StWLSensorPin'][index])
            else:
                raise NameError('incorrect Water Level Sensor Type!')
        else:
            # if no hardware, return random number
            return random.random()

    def sens_ba_status(self):  # returns amount of water in the barrel
        if gv.hw['WithHW']:
            if gv.hw['BaWLSensorType'][0] == 'min':
                return self.pe.input(gv.hw['BaWLSensorPin'][0])
            else:
                raise NameError('incorrect Water Level Sensor Type!')
        else:
            # if no hardware, return random number
            return random.random()
