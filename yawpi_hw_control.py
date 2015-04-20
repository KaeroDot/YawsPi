# vim modeline: vim: shiftwidth=4 tabstop=4
#=================================================================
# hardware abstraction layer
#=================================================================

# variables which should be accessed outside this class: see _init_vars()

# imports:
# timing for filling
from time import sleep
from time import time
# hw configuration:
# AND in check_gpio is import RPi.GPIO
# AND in _inithw is import Adafruit_MCP23017
# AND in _inithw is import MCP32008
# AND in _inithw is import BMP180
# AND in _inithw is import BH1750
# AND in _inithw is import DHT11


class yawpihw:
    def __init__(self):
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
        # initialize variables
        self._init_vars()
        # check hardware configuration:
        self._check_config()
        # test for GPIO
        self._check_gpio()
        # initialize hardware
        self._init_hw()

    def _init_vars(self):  # initialization of variables
        # outside this class only following variables should be accessed
        # revision number of raspberry pi:
        self.RPiRevision = ''
        # running on raspberry pi?:
        self.WithHW = 0
        # number of stations:
        self.StNo = len(self.hwc['St'])
        # status (on/off) of valves of stations:
        self.StStatus = [0] * len(self.hwc['St'])
        # status (on/off) of sensors:
        self.SeWLStatus = [0] * len(self.hwc['SeWL'])
        # status (on/off) of water source:
        self.SoStatus = 0
        # installed ambient sensors:
        self.Sensors = []

    def _check_config(self):  # check hw config
        # for pin collisions/correct configuration
        # check for port expander addresses duplicates:
        x = self.hwc['PeAddresses']
        if not len(set(x)) == len(x):
            raise NameError('hw config check: duplicates '
                            'in port expander adresses!')
        # check for ad converters addresses duplicates:
        x = self.hwc['AdcPins']
        if not len(set(x)) == len(x):
            raise NameError('hw config check: duplicates in '
                            'analog to digital pins!')
        # check duplicate pins on GPIO
        pinsgpio = self._get_all_gpio_pins()
        if not len(set(pinsgpio)) == len(pinsgpio):
            raise NameError('hw config check: duplicates in '
                            'pins assigned on gpio!')
        # find duplicates in port expander pins:
        pinspe = self._get_all_pe_pins()
        if not len(set(pinspe)) == len(pinspe):
            raise NameError('hw config check: duplicates in pins '
                            'assigned on port expanders!')
        # find duplicates in ad converter pins:
        pinsadc = self._get_all_adc_pins()
        if not len(set(pinsadc)) == len(pinsadc):
            raise NameError('hw config check: duplicates in pins '
                            'assigned on adcs!')
        # check number of stations is equal to number of sensors:
        if len(self.hwc['St']) + 1 != len(self.hwc['SeWL']):
            raise NameError('hw config check: different number '
                            'of stations and sensors!')
        # check temperature source:
        if self.hwc['SeTemp']:
            if self.hwc['SeTempSource'] == 'humid':
                if not self.hwc['SeHumid']:
                    raise NameError('temperature sensor set to read from '
                                    'humidity sensor but humidity sensor '
                                    'is missing!')
            elif self.hwc['SeTempSource'] == 'press':
                if not self.hwc['SePress']:
                    raise NameError('temperature sensor set to read from '
                                    'pressure sensor but pressure sensor '
                                    'is missing!')
            else:
                raise NameError('unknown source of temperature sensor!')
        # all hw is OK!
        print 'hardware configuration check is OK'
        # print summary:
        print 'number of port expanders: ' + str(len(self.hwc['PeAddresses']))
        print 'number of AD converters: ' + str(len(self.hwc['AdcPins']))
        print 'temperature sensor: ' + str(self.hwc['SeTemp'])
        print 'temperature sensor source: ' + self.hwc['SeTempSource']
        print 'rain sensor: ' + str(self.hwc['SeRain'])
        print 'humidity sensor: ' + str(self.hwc['SeHumid'])
        print 'pressure sensor: ' + str(self.hwc['SePress'])
        print 'illuminance sensor: ' + str(self.hwc['SeIllum'])
        print 'number of stations: ' + str(len(self.hwc['St']))
        print 'number of water level sensors: ' + str(len(self.hwc['SeWL']))
        return True

    def _get_all_gpio_pins(self):  # returns all pins addressed on GPIO
        pinsgpio = []
        # humidity sensor:
        if self.hwc['SeHumid']:
            pinsgpio.append(self.hwc['SeHumidPin'][1])
        # cable select pins of adc:
        for x in self.hwc['AdcPins']:
            pinsgpio.append(x[3])
        return pinsgpio

    def _get_all_pe_pins(self):  # returns all pins addressed on port expanders
        pinspe = []
        # source pin:
        pinspe.append(self.hwc['So']['Pin'])
        # valve pins:
        for x in self.hwc['St']:
            pinspe.append(x['Pin'])
        # water level sensor pins:
        for x in self.hwc['SeWL']:
            if x['Type'] == 'min' or x['Type'] == 'max':
                pinspe.append(x['Pin'])
            elif x['Type'] == 'minmax':
                pinspe.append(x['MinPin'])
                pinspe.append(x['MaxPin'])
            elif x['Type'] == 'grad':
                pinspe.append(x['OnOffPin'])
        return pinspe

    def _get_all_adc_pins(self):  # returns all pins addressed on ad converters
        pinsadc = []
        # grad water level sensors:
        for x in self.hwc['SeWL']:
            if x['Type'] == 'grad':
                pinsadc.append(x['ValuePin'])
        # sensor pins:
        if self.hwc['SeRain']:
            pinsadc.append(self.hwc['SeRainPin'])
        return pinsadc

    def _check_gpio(self):  # tests if gpio present, else simulated mode is set
        # self.WithHW  - if set, runs with pumps and valves and real sensors,
        # if unset, no hardware access is performed. If import GPIO failes it
        # is unset:
        self.WithHW = 1
        try:
            import RPi.GPIO as GPIO  # RPi general purpose input/output library
            self.gpio = GPIO
        except (ImportError, RuntimeError):
            # for different python versions different error occurs
            # version 2.7.3: ImportError occurs
            # some other version: RuntimeError occurs
            self.WithHW = 0

    def _init_hw(self):  # initialization of hw
        # set RPi revision
        if self.WithHW:
            self.gpio.setmode(self.gpio.BOARD)
            self.RPiRevision = self.gpio.RPI_REVISION
        else:
            self.RPiRevision = 'no hardware mode'

        # import humidity sensor:
        if self.WithHW:
            if self.hwc['SeHumid']:
                from DHT11 import DHT11
                self.humid = DHT11(self.hwc['SeHumidPin'][1])
                self.Sensors.append('humid')

        # import pressure sensor:
        if self.WithHW:
            if self.hwc['SePress']:
                from BMP180 import BMP180
                self.press = BMP180(self.RPiRevision - 1, 3)
                self.Sensors.append('press')

        # import illuminance sensor:
        if self.WithHW:
            if self.hwc['SeIllum']:
                from BH1750 import BH1750
                self.illum = BH1750(self.RPiRevision - 1,
                                    self.hwc['SeIllumAddrToHigh'])
                self.Sensors.append('illum')

        # import port expanders and ad converters libraries:
        if self.WithHW:
            # port expanders:
            from Adafruit_MCP230XX import Adafruit_MCP230XX
            self.pe = []
            for id in self.hwc['PeAddresses']:
                self.pe.append(Adafruit_MCP230XX(address=id, num_gpios=16))

            # ad converter:
            from MCP3008 import MCP3008
            # self.adc = class_MCP32008(address=self.hwc['PeAddress'])
            self.adc = []
            for id in self.hwc['AdcPins']:
                self.adc.append(MCP3008(id[0], id[1], id[2], id[3]))

            # XXX check IDs of stations and sensors!
            # what does it means? deprecated?

            # setup port expanders:
            # first set all as inputs
            for p in range(1, len(self.pe) + 1):
                for n in range(16):
                    self._pin_config((p, n), 1)
            # set water source port as output:
            self._pin_config(self.hwc['So']['Pin'], 0)
            # set valve ports as output:
            for x in self.hwc['St']:
                self._pin_config(x['Pin'], 0)
            # set pins on 'grad' sensors to output:
            for x in self.hwc['SeWL']:
                if x['Type'] == 'grad':
                    self._pin_config(x['OnOffPin'], 0)
            # and switch all off:
            self.so_switch(0)                   # switch off pump
            for x in range(len(self.hwc['St'])):  # switch off valves
                self.st_switch(x, 0)
            for x in range(len(self.hwc['SeWL'])):  # switch off all sensors
                self.se_switch(x, 0)

    def _pin_config(self, pin, direction):  # configure pin as output or input
        # direction: 0 == output, 1 == input
        if pin[0] == 0:
            # GPIO pin:
            # XXX finish it
            pass
        elif pin[0] > 0:
            # port expanders:
            if direction:
                tmp = self.pe[pin[0] - 1].INPUT
            else:
                tmp = self.pe[pin[0] - 1].OUTPUT
            self.pe[pin[0] - 1].config(pin[1], tmp)
        else:
            # ad converters: no action:
            pass

    def _pin_pullup(self, pin, value):  # configure pullup of a pin
        if pin[0] == 0:
            # GPIO pin:
            # XXX finish it
            pass
        elif pin[0] > 0:
            # port expanders:
            if value:
                self.pe[pin[0] - 1].pullup(pin[1], 1)
            else:
                self.pe[pin[0] - 1].pullup(pin[1], 0)
        else:
            # ad converters: no action:
            pass

    def _pin_set(self, pin, value):  # set pin to a value
        if pin[0] == 0:
            # GPIO pin:
            # XXX finish it
            pass
        elif pin[0] > 0:
            # port expanders:
            self.pe[pin[0] - 1].output(pin[1],  value)
        else:
            # ad converters: no action:
            pass

    def _pin_get(self, pin):  # returns value of a pin
        # pin is tuple with two numbers
        if pin[0] == 0:
            # GPIO pin
            pass
        elif pin[0] > 0:
            # port expanders:
            return self.pe[pin[0] - 1].input(pin[1])
        else:
            # ad converters:
            return self.adc[-1 * pin[0] - 1].readadcv(pin[1], 5) / 5

    def so_switch(self, value):  # set water source on or off
        if self.WithHW:
            if value:
                # switch on
                self._pin_set(self.hwc['So']['Pin'], 1)
                self.SoStatus = 1
            else:
                # switch off
                self._pin_set(self.hwc['So']['Pin'], 0)
                self.SoStatus = 0

    def st_switch(self, index,  value):  # sets station valve on or off
        if index < 0 or index > len(self.hwc['St']) - 1:
            raise NameError('incorrect valve index')
        if self.WithHW:
            if value:
                # switch valve on
                self._pin_set(self.hwc['St'][index]['Pin'], 1)
                self.StStatus[index] = 1
            else:
                # switch valve off
                self._pin_set(self.hwc['St'][index]['Pin'], 0)
                self.StStatus[index] = 0

    def se_switch(self, index, value):  # switch sensor on or off
        if index < 0 or index > len(self.hwc['SeWL']) - 1:
            raise NameError('incorrect sensor index')
        if self.WithHW:
            if self.hwc['SeWL'][index]['Type'] == 'none':
                # if no sensor do nothing:
                if value:
                    self.SeWLStatus[index] = 1
                else:
                    self.SeWLStatus[index] = 0
            elif self.hwc['SeWL'][index]['Type'] == 'min':
                # set pullup:
                pin = self.hwc['SeWL'][index]['Pin']
                if value:
                    self.SeWLStatus[index] = 1
                    self._pin_pullup(pin, 1)
                else:
                    self.SeWLStatus[index] = 0
                    self._pin_pullup(pin, 0)
            elif self.hwc['SeWL'][index]['Type'] == 'max':
                # set pullup:
                pin = self.hwc['SeWL'][index]['Pin']
                if value:
                    self.SeWLStatus[index] = 1
                    self._pin_pullup(pin, 1)
                else:
                    self.SeWLStatus[index] = 0
                    self._pin_pullup(pin, 0)
                # set pullup:
            elif self.hwc['SeWL'][index]['Type'] == 'minmax':
                # set pullup for both pins:
                pin1 = self.hwc['SeWL'][index]['MinPin']
                pin2 = self.hwc['SeWL'][index]['MaxPin']
                if value:
                    self.SeWLStatus[index] = 1
                    self._pin_pullup(pin1, 1)
                    self._pin_pullup(pin2, 1)
                else:
                    self.SeWLStatus[index] = 0
                    self._pin_pullup(pin1, 0)
                    self._pin_pullup(pin2, 0)
            elif self.hwc['SeWL'][index]['Type'] == 'grad':
                if value:
                    self._pin_set(self.hwc['SeWL'][index]['OnOffPin'], 1)
                    self.SeWLStatus[index] = 1
                else:
                    self._pin_set(self.hwc['SeWL'][index]['OnOffPin'], 0)
                    self.SeWLStatus[index] = 0
            else:
                raise NameError('unknown Water Level Sensor Type!')
        else:
            # if no hardware, do nothing
            pass

    def so_level(self):  # returns water level of water in the water source
        # barrel sensor is the last one
        if self.hwc['So']['Cap'] == -1:
            return 1
        else:
            return self.se_level(len(self.hwc['SeWL']) - 1)

    def se_level(self, index):  # returns water level of water source
    # returns amount of water sensed by the sensor, returned value is in
    # interval <0, 1> (empty to full)
        if index < 0 or index > len(self.hwc['SeWL']) - 1:
            raise NameError('incorrect sensor index: ' + str(index))
        if self.WithHW:
            # first switch sensor on:
            self.se_switch(index, 1)
            # let voltages stabilize:
            sleep(0.1)
            # second get sensor value
            if self.hwc['SeWL'][index]['Type'] == 'none':
                # if no sensor consider station always empty:
                val = 0
            elif self.hwc['SeWL'][index]['Type'] == 'min':
                val = self._pin_get(self.hwc['SeWL'][index]['Pin'])
                if val:  # because PE driver returns various values
                    val = 1
                else:
                    val = 0
            elif self.hwc['SeWL'][index]['Type'] == 'max':
                val = self._pin_get(self.hwc['SeWL'][index]['Pin'])
                if val:  # because PE driver returns various values
                    val = 0
                else:
                    val = 1
            elif self.hwc['SeWL'][index]['Type'] == 'minmax':
                #read both sensors
                x = self._pin_get(self.hwc['SeWL'][index]['MinPin'])
                y = self._pin_get(self.hwc['SeWL'][index]['MaxPin'])
                # decide station status:
                if x == 0:
                    # min sensor is switched, station is empty
                    val = 0
                elif y == 0:  # because PE driver returns various values
                    # max sensor is switched, station is full
                    val = 1
                else:
                    # else station is half empty
                    val = 0.5
            elif self.hwc['SeWL'][index]['Type'] == 'grad':
                sleep(0.1)
                # first reading throw away, than read three times and return
                # average:
                val = self._pin_get(self.hwc['SeWL'][index]['ValuePin'])
                val = self._pin_get(self.hwc['SeWL'][index]['ValuePin'])
                val = val + self._pin_get(self.hwc['SeWL'][index]['ValuePin'])
                val = val + self._pin_get(self.hwc['SeWL'][index]['ValuePin'])
                val = val / 3
            else:
                raise NameError('unknown Water Level Sensor Type!')
            # third switch sensor off:
            self.se_switch(index, 0)
            # fourth return value:
            return val
        else:
            # if no hardware, return part of hour
            # what is it? XXX
            ##hour = time.time() // 3600
            ##rest = time.time() - hour * 3600
            ##minute = rest // 60.0
            ##return minute / 60.0
            return 0.05

    def fill_time(self, index):  # return filling time (s) of a station
        V = self.hwc['St'][index]['Cap']   # volume
        O = self.hwc['So']['FlowRate'][0]  # offset
        R = self.hwc['So']['FlowRate'][1]  # rate
        return (V - O) / R

    def st_fill(self, index, upthreshold):  # fill water into one station
        if self.WithHW:
            # index is index of station, upthreshold is value if reached,
            # station is considered filled.
            # get filling time in seconds according to station capacity:
            filltime = self.fill_time(index)
            # type of sensor
            sensortype = self.hwc['SeWL'][index]['Type']
            stsettlet = self.hwc['St'][index]['SettleT']
            sosettlet = self.hwc['So'][index]['SettleT']
            self.st_switch(index, 1)  # switch valve on
            sleep(stsettlet)  # wait to valve settle
            self.so_switch(1)  # set pump on
            tmp = time.time()
            if sensortype == 'none':
                # if no sensor, just wait filltime:
                sleep(filltime)
            else:
                # if sensor, wait for sensor showing full or if time is 1.1
                # times greater than filltime
                endtime = time.time() + filltime * 1.1
                while time.time() < endtime:
                    # periodically detect wl:
                    if self.se_level(index) > upthreshold:
                        break
                    else:
                        # check sensor every 0.05 second:
                        # XXX wait time could be changed?
                        sleep(0.05)
            self.so_switch(0)            # set pump off
            realfilltime = time.time() - tmp
            sleep(sosettlet)                # wait to stop the water flow
            self.st_switch(index, 0)        # switch valve off
            sleep(stsettlet)                # wait to valve settle
            return realfilltime
        else:
            # if no hardware, return some dummy value:
            return 2

    def se_temp(self):  # return temperature
        if self.WithHW and self.hwc['SeTemp']:
            if self.hwc['SeTempSource'] == 'humid':
                return self.humid.meas()[1]
            if self.hwc['SeTempSource'] == 'press':
                return self.press.meas_temp()
        return -300

    def se_rain(self):  # return rain status
        if self.WithHW and self.hwc['SeRain']:
            value = self._pin_get(self.hwc['SeRainPin'])
            # rain is only if voltage is greater than 0.2:
            return int(value > 0.2)
        return -300

    def se_humid(self):  # return humidity
        if self.WithHW and self.hwc['SeHumid']:
            return self.humid.meas()[0]
        return -300

    def se_press(self):  # return pressure
        if self.WithHW and self.hwc['SePress']:
            self.press.meas_temp()
            return self.press.meas_press()
        return -300

    def se_illum(self):  # return illuminance
        if self.WithHW and self.hwc['SeIllum']:
            return self.illum.meas()
        return -300

    def clean_up(self):  # cleans GPIO
        if self.WithHW:
            self.gpio.cleanup()


if __name__ == "__main__":  # this routine checks system
    try:
        # this routine is not used during normal run
        # initialize:
        print 'initialization:'
        hw = yawpihw()
        print '----------'
        print 'hw mode: ' + str(hw.WithHW)
        # print all sensors:
        print '----------'
        print 'ambient sensors:'
        print 'temp=' + str(hw.se_temp())
        print 'humid=' + str(hw.se_humid())
        print 'press=' + str(hw.se_press())
        print 'rain=' + str(hw.se_rain())
        print 'illum=' + str(hw.se_illum())
        # check valves:
        print '----------'
        print 'station valves one by one on and off:'
        for i in range(hw.StNo):
            print 'valve of station ' + str(i) + ' on...'
            hw.st_switch(i, 1)
            sleep(1)
            print 'valve of station ' + str(i) + ' off...'
            hw.st_switch(i, 0)
            sleep(1)
        # check source:
        print '----------'
        print 'set valve of station 0 on and source on...'
        print 'valve of station 0 on...'
        hw.st_switch(0, 1)
        sleep(1)
        print 'source on...'
        hw.so_switch(1)
        sleep(1)
        print 'source off...'
        hw.so_switch(0)
        sleep(1)
        print 'valve of station 0 off...'
        hw.st_switch(0, 0)
        # print water level sensors:
        print '----------'
        print 'sensors:'
        while True:
            for i in range(hw.StNo):
                print 'sensor of station ' + str(i) + \
                      ', type ' + hw.hwc['SeWL'][i]['Type'] + \
                      ': ' + str(hw.se_level(i))
            print 'source: ' + str(hw.se_level(i + 1))
            sleep(0.5)
    except KeyboardInterrupt:
        print ' -- user interrupt'
