#!/usr/bin/python

# Based on Adafruits libraries, license is inherited

import time
import RPi.GPIO as GPIO

MAXADCNUM = 7

class K_MCP32008(object):
    
    def __init__(self, clockpin, mosipin, misopin, cspin):
        self.clockpin = clockpin
        self.mosipin = mosipin
        self.misopin = misopin
        self.cspin = cspin

        GPIO.setmode(GPIO.BCM)

        # set up the SPI interface pins
        GPIO.setup(self.mosipin, GPIO.OUT)
        GPIO.setup(self.misopin, GPIO.IN)
        GPIO.setup(self.clockpin, GPIO.OUT)
        GPIO.setup(self.cspin, GPIO.OUT)

# read SPI data from MCP3208 chip, 8 possible adc's (0 thru 7)
    def readadc(self, adcnum):
        assert adcnum >=0 and adcnum <= MAXADCNUM, "Value of adcnum out of bounds"

        GPIO.output(self.cspin, True) # select SPI device

        GPIO.output(self.clockpin, False) # start clock low
        GPIO.output(self.cspin, False) # bring CS low

        commandout = adcnum
        commandout |= 0x18 # start bit + single-ended bit
        commandout <<= 3 # we only need to send 5 bits here
        for i in range(5):
                if (commandout & 0x80):
                        GPIO.output(self.mosipin, True)
                else:
                        GPIO.output(self.mosipin, False)
                commandout <<= 1
                GPIO.output(self.clockpin, True)
                GPIO.output(self.clockpin, False)

        adcout = 0

        # read in one empty bit, one null bit and 12 ADC bits
        for i in range(14):
                GPIO.output(self.clockpin, True)
                GPIO.output(self.clockpin, False)
                adcout <<= 1
                if (GPIO.input(self.misopin)):
                        adcout |= 0x1

        GPIO.output(self.cspin, True)
        
        adcout >>= 1 # first bit is 'null' so drop it
        return adcout

if __name__ == '__main__':
    # Note that bitbanging SPI is incredibly slow on the Pi as its not
    # a RTOS - reading the ADC takes about 30 ms (~30 samples per second)
    # which is awful for a microcontroller but better-than-nothing for Linux

    # change to the value of the voltage reference connected to the ADC:
    VOLTREF = 5
    # change values as desired - they're the pins connected from the SPI port on the ADC to the RPi
    mcp = K_MCP32008(clockpin = 11, misopin = 9, mosipin = 10, cspin = 27)

    # maximal value of the analog to digital converter:
    MAXDIG = 4095

    ret=range(8)
    print "|  adcnum: \t#0 \t #1 \t #2 \t #3 \t #4 \t #5 \t #6 \t #7\t|"
    print "---------------------------------------------------------------------------------"
    while True:
        print "| digital: \t",
        for adcnum in range(8):
            ret[adcnum] = mcp.readadc(adcnum)
            print ret[adcnum],"\t",
        print "|"
        print "| voltage: \t",
        for adcnum in range(8):
            voltage = VOLTREF * ret[adcnum] / MAXDIG
            print round(voltage,3),"V\t",
        print "|"
        print "---------------------------------------------------------------------------------"
        time.sleep(1)
