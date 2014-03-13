#!/usr/bin/python

# Copyright 2012 Daniel Berlin (with some changes by Adafruit Industries/Limor Fried)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal  MCP230XX_GPIO(1, 0xin
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from Adafruit_I2C import Adafruit_I2C
import smbus
import time

MCP23016_GP0      = 0x00
MCP23016_GP1      = 0x01
MCP23016_OLAT0    = 0x02
MCP23016_OLAT1    = 0x03
MCP23016_IOPOL0   = 0x04
MCP23016_IOPOL1   = 0x05
MCP23016_IODIR0   = 0x06
MCP23016_IODIR1   = 0x07
MCP23016_INTCAP0  = 0x08
MCP23016_INTCAP1  = 0x09
MCP23016_IOCON0   = 0x0A
MCP23016_IOCON1   = 0x0B

class Adafruit_MCP23016(object):
    OUTPUT = 0
    INPUT = 1

    def __init__(self, address):
        self.i2c = Adafruit_I2C(address=address)
        self.address = address

        # set defaults
        self.i2c.write8(MCP23016_IODIR0, 0xFF)  # all inputs on port A
        self.i2c.write8(MCP23016_IODIR1, 0xFF)  # all inputs on port B
        self.direction = self.i2c.readU8(MCP23016_IODIR0)
        self.direction |= self.i2c.readU8(MCP23016_IODIR1) << 8

    def _changebit(self, bitmap, bit, value):
        assert value == 1 or value == 0, "Value is %s must be 1 or 0" % value
        if value == 0:
            return bitmap & ~(1 << bit)
        elif value == 1:
            return bitmap | (1 << bit)

    def _readandchangepin(self, port, pin, value, currvalue = None):
        assert pin >= 0 and pin < 16, "Pin number %s is invalid, only 0-%s are valid" % (pin, self.num_gpios)
        #assert self.direction & (1 << pin) == 0, "Pin %s not set to output" % pin
        if not currvalue:
             currvalue = self.i2c.readU8(port)
        newvalue = self._changebit(currvalue, pin, value)
        self.i2c.write8(port, newvalue)
        return newvalue


    # Set pin to either input or output mode
    def config(self, pin, mode):
        if (pin < 8):
            self.direction = self._readandchangepin(MCP23016_IODIR0, pin, mode)
        else:
            self.direction |= self._readandchangepin(MCP23016_IODIR1, pin-8, mode) << 8

        return self.direction

    def output(self, pin, value):
        # assert self.direction & (1 << pin) == 0, "Pin %s not set to output" % pin
        if (pin < 8):
            self.outputvalue = self._readandchangepin(MCP23016_GP0, pin, value, self.i2c.readU8(MCP23016_OLAT0))
        else:
            self.outputvalue = self._readandchangepin(MCP23016_GP1, pin-8, value, self.i2c.readU8(MCP23016_OLAT1)) << 8

        return self.outputvalue


        self.outputvalue = self._readandchangepin(MCP23016_IODIR0, pin, value, self.outputvalue)
        return self.outputvalue

    def input(self, pin):
        assert pin >= 0 and pin < 16, "Pin number %s is invalid, only 0-%s are valid" % (pin, self.num_gpios)
        assert self.direction & (1 << pin) != 0, "Pin %s not set to input" % pin
        value = self.i2c.readU8(MCP23016_GP0)
        value |= self.i2c.readU8(MCP23016_GP1) << 8
        return value & (1 << pin)

    def readU16(self):
        lo = self.i2c.readU8(MCP23016_OLAT0)
        hi = self.i2c.readU8(MCP23016_OLAT1)
        return((hi << 8) | lo)

    def readS16(self):
        lo = self.i2c.readU8(MCP23016_OLAT0)
        hi = self.i2c.readU8(MCP23016_OLAT1)
        if (hi > 127): hi -= 256
        return((hi << 8) | lo)

    def write16(self, value):
        self.i2c.write8(MCP23016_OLAT0, value & 0xFF)
        self.i2c.write8(MCP23016_OLAT1, (value >> 8) & 0xFF)

# RPi.GPIO compatible interface for MCP23016

class MCP23016_GPIO(object):
    OUT = 0
    IN = 1
    BCM = 0
    BOARD = 0
    def __init__(self, busnum, address):
        self.chip = Adafruit_MCP23016(busnum, address)
    def setmode(self, mode):
        # do nothing
        pass
    def setup(self, pin, mode):
        self.chip.config(pin, mode)
    def input(self, pin):
        return self.chip.input(pin)
    def output(self, pin, value):
        self.chip.output(pin, value)
    def pullup(self, pin, value):
        self.chip.pullup(pin, value)


if __name__ == '__main__':
    mcp = Adafruit_MCP23016(address = 0x20) # MCP23008

    # Set pin 0 to output (you can set pins 0..15 this way)
    mcp.config(0, mcp.OUTPUT)

    # Set pin 1 to input
    mcp.config(1, mcp.INPUT)

    # Read input pin and display the results
    print "Pin 1 = %d" % (mcp.input(3) >> 3)

    # Python speed test on output 0 toggling at max speed
    print "Starting blinky on pin 0 (CTRL+C to quit)"
    while (True):
        mcp.output(0, 1)  # Pin 0 High
        time.sleep(0.05);
        mcp.output(0, 0)  # Pin 0 Low
        time.sleep(0.05);
        # Read input pin and display the results
        #print "Pin 1 = %d" % (mcp.input(1) >> 3)
        print "Pin 1: " + str(mcp.input(1))
