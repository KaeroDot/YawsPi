#=================================================================
# hardware abstraction layer
#=================================================================

# variables which should be used outside this class: see _init_vars()

# imports:
# gv - 'global vars' - an empty module, used for storing vars (as attributes),
# that need to be 'global' across threads and between functions and classes:
import gv
# random numbers for sensors when hardware is not present:
import random
# timing for filling
import time
# hw configuration:
# AND in check_gpio is import RPi.GPIO
# AND in _inithw is import Adafruit_MCP23017
# AND in _inithw is import class_MCP32008


class yawpihw:
    def __init__(self):
        # test for GPIO
        self._check_gpio()
        # load hardware configuration:
        try:
            from yawpi_hw_config import yawpi_hw_config
            # for different python versions different error occurs
            # version 2.7.3: ImportError occurs
            # some other version: RuntimeError occurs
        except (ImportError, RuntimeError):
            # if missing, load demo configuration:
            from yawpi_hw_config_demo import yawpi_hw_config
        self.hwc = yawpi_hw_config()
        # check hardware configuration:
        self._check_config()
        # initialize variables
        self._init_vars()
        # initialize hardware
        self._init_hw()

    def _init_vars(self):  # initialization of variables
        # init variables:
        self.RPiRevision = ''
        self.WithHW = 0
        # number of stations:
        self.StNo = len(self.hwc['St'])
        # status (on/off) of valves of stations:
        self.StStatus = [0] * len(self.hwc['St'])
        # status (on/off) of sensors (has sense only for grad sensors)
        self.SeWLStatus = [0] * len(self.hwc['SeWL'])
        # status (on/off) of water source:
        self.SoStatus = 0

    def _check_config(self):  # check hw config
        # for pin collisions/correct configuration
        # check for port expander adresses duplicates:
        x = self.hwc['PeAddresses']
        if not len(set(x)) == len(x):
            raise NameError('duplicates in port expander adresses!')
        x = self.hwc['AdcPins']
        if not len(set(x)) == len(x):
            raise NameError('duplicates in analog to digital pins!')
        # get all pins in one list:
        pinspe = []
        pinsadc = []
        pinspe.append(self.hwc['So']['Pin'])
        for x in self.hwc['St']:
            pinspe.append(x['Pin'])
        for x in self.hwc['SeWL']:
            if x['Type'] == 'min' or x['Type'] == 'max':
                pinspe.append(x['Pin'])
            elif x['Type'] == 'minmax':
                pinspe.append(x['MinPin'])
                pinspe.append(x['MaxPin'])
            elif x['Type'] == 'grad':
                pinspe.append(x['OnOffPin'])
                pinsadc.append(x['ValuePin'])
        # find duplicates in all pins:
        if not len(set(pinspe)) == len(pinspe):
            raise NameError('duplicates in pins assigned on port expanders!')
        if not len(set(pinsadc)) == len(pinsadc):
            raise NameError('duplicates in pins assigned on adcs!')
        print 'hardware configuration check is OK'
        return True

    def _check_gpio(self):  # tests if gpio present, else simulated mode is set
        # self.WithHW  - if set, runs with pumps and valves and real sensors,
        # if unset, no hardware access is performed. If import GPIO failes it
        # is unset:
        self.WithHW = 1
        try:
            import RPi.GPIO as GPIO  # RPi general purpose input/output library
            self.gpio = GPIO
        # for different python versions different error occurs
        # version 2.7.3: ImportError occurs
        # some other version: RuntimeError occurs
        except (ImportError, RuntimeError):
            self.WithHW = 0

    def _init_hw(self):  # initialization of hw
        # set RPi revision
        if self.WithHW:
            self.gpio.setmode(self.gpio.BOARD)
            self.RPiRevision = self.gpio.RPI_REVISION
        else:
            self.RPiRevision = 'no hardware mode'

        # import port expanders and ad converters libraries:
        if self.WithHW:
            # port expanders:
            from Adafruit_MCP230xx import Adafruit_MCP230xx
            self.pe = []
            for id in self.hwc['PeAddresses']:
                self.pe.append(Adafruit_MCP230xx(address=id, num_gpios=16))
            # ad converter:
            from K_MCP3008 import K_MCP3008
            # self.adc = class_MCP32008(address=self.hwc['PeAddress'])
            self.adc = []
            for id in self.hwc['AdcPins']:
                self.adc.append(K_MCP3008(id))

            # XXX check IDs of stations and sensors!

            # setup port expanders:
            # first set all as inputs
            for p in self.pe:
                for x in range(16):
                    self.p[id].config(x, self.p[id].INPUT)
            # set water source port as output:
            x = self.hwc['So']['Pin']
            self.pe[x[0]].config(x[1], self.pe[x[0]].OUTPUT)
            # set valve ports as output:
            for x in self.hwc['St']:
                t = x['Pin']
                self.pe[t[0]].config(t[1], self.pe[t[0]].OUTPUT)
            # set switches on 'grad' sensors to output:
            for x in self.hwc['SeWL']:
                if x['SeWL'] == 'grad':
                    t = x['OnOffPin']
                    self.pe[t[0]].config(t[1], self.pe[t[0]].OUTPUT)

            # and switch all off:
            self.pump_switch(0)                   # switch off pump
            for x in range(len(self.hwc['St'])):  # switch off valves
                self.valve_switch(x, 0)
            for x in range(len(self.hwc['SeWL'])):  # switch off grad sensors
                if x['SeWL'] == 'grad':
                    self.sens_wl_switch(x, 0)

    def _set_pin(self, pin, state):  # set pin on port expander to a value
        # this function is only for better readability
        # pin is tuple with two numbers
        self.pe[pin[0]].output(pin[1],  state)

    def _get_pin(self, pin):  # returns value of a pin
        # this function is only for better readability
        # pin is tuple with two numbers
        return self.pe[pin[0]].input(pin[1])

    def so_switch(self, state):  # set water source on or off
        if self.WithHW:
            if state:
                # switch on
                self._set_pin(self.hwc['Pu']['Pin'], 1)
                self.SoStatus = 1
            else:
                # switch off
                self._set_pin(self.hwc['Pu']['Pin'], 0)
                self.SoStatus = 0

    def st_switch(self, index,  state):  # sets station valve on or off
        if index < 0 or index > len(self.hwc['St']) - 1:
            raise NameError('incorrect valve index')
        if self.WithHW:
            if state:
                # switch valve on
                self._set_pin(self.hwc['St'][index]['ValvePin'], 1)
                self.StStatus[index] = 1
            else:
                # switch valve off
                self._set_pin(self.hwc['St'][index]['ValvePin'], 0)
                self.StStatus[index] = 0

    def se_switch(self, index, state):  # set sensor on or off
        if index < 0 or index > len(self.hwc['SeWL']) - 1:
            raise NameError('incorrect sensor index')
        if not self.hwc['SeWL'][index]['Type'] == 'grad':
            raise NameError('incorrect sensor type to switch')
        if self.WithHW:
            if state:
                # switch sensor on
                self._set_pin(self.hwc['SeWL'][index]['OnOffPin'], 1)
                self.SeWLStatus[index] = 1
            else:
                # switch sensor off
                self._set_pin(self.hwc['SeWL'][index]['OnOffPin'], 0)
                self.SeWLStatus[index] = 0

    def so_level(self):  # returns water level of water in the water source
        # barrel sensor is always the last one
        if self.hwc['So']['Cap'] == -1:
            return 1
        else:
            return self.se_level(len(self.hwc['SeWL']) - 1)

    def se_level(self, index):  # returns water level of water source
    # returns amount of water sensed by the sensor, returned value is in
    # interval <0, 1> (empty to full)
        if index < 0 or index > len(self.hwc['SeWL']) - 1:
            raise NameError('incorrect sensor index')
        if self.WithHW:
            if self.hwc['SeWL'][index]['Type'] == 'none':
                # if no sensor consider station always empty:
                return 0
            elif self.hwc['SeWL'][index]['Type'] == 'min':
                return self._get_pin(self.hwc['SeWL'][index]['Pin'])
            elif self.hwc['SeWL'][index]['Type'] == 'max':
                return not self._get_pin(self.hwc['SeWL'][index]['Pin'])
            elif self.hwc['SeWL'][index]['Type'] == 'minmax':
                #read both sensors
                x = self._get_pin(self.hwc['SeWL'][index]['MinPin'])
                y = self._get_pin(self.hwc['SeWL'][index]['MaxPin'])
                # decide station status:
                if x == 0:
                    # min sensor is zero, station is empty
                    return 0
                elif y == 1:
                    # max sensor is one, station is full
                    return 1
                else:
                    # else station is half empty
                    return 0.5
            elif self.hwc['SeWL'][index]['Type'] == 'grad':
                self.sens_wl_switch(index, 1)
                # get adc value
                # XXX XXXXXXXXXX XXX
                self.sens_wl_switch(index, 0)
            else:
                raise NameError('incorrect Water Level Sensor Type!')
        else:
            # if no hardware, return random number
            return random.random()

    def fill_time(self, index):  # return filling time (s) of a station
        V = self.hwc['St'][index]['Cap']   # volume
        O = self.hwc['So']['FlowRate'][0]  # offset
        R = self.hwc['So']['FlowRate'][1]  # rate
        return (V - O) / R

    def st_fill(self, index, upthreshold):  # fill water into one station
        # index is index of station, upthreshold is value if reached, station is
        # considered filled
        # get filling time in seconds according to station capacity:
        filltime = self.fill_time(index)
        # type of sensor
        sensortype = self.hwc['SeWL'][index]['Type']
        stsettlet = self.hwc['St'][index]['SettleT']
        sosettlet = self.hwc['So'][index]['SettleT']
        self.st_switch(index, 1)  # switch valve on
        time.sleep(stsettlet)  # wait to valve settle
        self.so_switch(1)  # set pump on
        tmp = time.time()
        if sensortype == 'none':
            # if no sensor, just wait filltime:
            time.sleep(filltime)
        else:
            # if sensor, wait for sensor showing full or if time is 1.1 times
            # greater than filltime
            endtime = time.time() + filltime * 1.1
            while time.time() < endtime:
                # periodically detect wl:
                if self.se_level(index) > upthreshold:
                    break
                else:
                    # check sensor every 0.05 second:
                    # XXX wait time could be changed?
                    time.sleep(0.05)
        self.so_switch(0)            # set pump off
        realfilltime = time.time() - tmp
        time.sleep(sosettlet)             # wait to stop the water flow
        self.st_switch(index, 0)  # switch valve off
        time.sleep(stsettlet)             # wait to valve settle
        return realfilltime

    def se_temp(self):  # return temperature
        if self.hwc['SeTemp']:
            return 1            # XXX finish it
        else:
            return -300

    def se_rain(self):  # return rain status
        if self.hwc['SeRain']:
            return 1            # XXX finish it
        else:
            return -300

    def se_humid(self):  # return humidity
        if self.hwc['SeHumid']:
            return 1            # XXX finish it
        else:
            return -300

    def se_press(self):  # return pressure
        if self.hwc['SePress']:
            return 1            # XXX finish it
        else:
            return -300

    def clean_up(self):  # cleans GPIO
        if self.WithHW:
            self.gpio.cleanup()
