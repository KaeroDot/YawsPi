# -*- coding: utf-8 -*-

"""
Module for initialising and reading Soil Moisture Sensor using modbus
Device can report value 0.1 s after power up, but the value is underestimated.
Delay of 2 seconds is required to get proper value.
"""

# imports:
import minimalmodbus
from time import sleep


class SMSens(object):
    """ Class for Soil moisture sensor using modbus.
    """
    def __init__(self,
                 Address,
                 Register=1,
                 TTY='/dev/ttyUSB0',
                 Baudrate=9600):
        """ Initialize class.
        \param Address - addres of the modbus sensor
        \param Register - register of the modbus sensor for humidity
        \param TTY - linux device of the RS232-RS485 converter
        \param Baudrate - baudrate for TTY port of the RS232-RS485 converter
        \return Nothing
        """
        self.address = int(Address)
        self.register = int(Register)
        self.TTY = TTY
        self.baudrate = int(Baudrate)

        # initialize instrument:
        self.__init_instr__()

    def __init_instr__(self):
        """ Initialize instrument
        \param Nothing
        \return Nothing
        """
        self.instrument = minimalmodbus.Instrument(self.TTY, self.address)
        self.instrument.serial.baudrate = self.baudrate

    def read(self):
        """ Read sensor data
        \param Nothing
        \return float: Sensor value (0,1)
        """
        try:
            h = self.instrument.read_register(self.register, 1)
        except minimalmodbus.InvalidResponseError:
            # error in reading, bad data, raised by:
            #  File "/home/pi/.local/lib/python3.7/site-packages/minimalmodbus.py", line 1756, in _extract_payload
            #  raise InvalidResponseError(text)
            #  minimalmodbus.InvalidResponseError: Checksum error in rtu mode
            h = -1
        return h/100

    def readdress(self, newaddress):
        """ Readdress device
        \param newaddress
        \return Nothing
        """
        try:
            self.instrument.write_register(256, newaddress, functioncode=6)
        except:
            print('expected error was ignored...')
        # delete existing instrument
        del self.instrument
        # needed time delay for device to readdress
        sleep(2)
        # initialize instrument at new address
        self.address = newaddress
        self.__init_instr__()


if __name__ == "__main__":  # routine lists devices and readdress
    """ List or readdress connected devices
        -list       : find all connected devices
        -re X       : readdress device at address X
        -cont X     : continuously read device at address X
    """
    import sys
    # get input parameter
    try:                      # catch the error when no input parameter
        par = sys.argv[1]      # get input parameter
    except:                   # if no input parameter
        par = ""

    par = par.lower()       # input parameter to lowercase

    # permited input parameters:
    permittedpar = ['-list', '-re', '-cont']
    if par not in permittedpar:
        # print help if unknown or empty input parameter
        print("Help: add input parameter, one of:")
        print("-list        find all connected devices")
        print("-re X Y      readdress device at address X to address Y")
        print("-cont X      continuously read device at address X")
    else:
        foundaddress = -1
        if par == "-list":
            # list connected devices
            for address in range(0, 256):
                # setup humidity sensor:
                try:
                    # intialize device
                    instrument = SMSens(address,  1, '/dev/ttyUSB0', 9600)
                    # try to read soil moisture
                    h = instrument.read()
                    # if no error happened, mark found device and exit loop
                    foundaddress = address
                    print('\ndevice found at address ' + str(address) +
                          ' (response was ' + str(h) + ')')
                except KeyboardInterrupt:
                    print('user interrupt')
                    break
                except:
                    # cannot read from address, just continue with another:
                    #  print('device not found at address ' + str(address))
                    print('.', end='')
                    sys.stdout.flush()  # refresh display
                    #  pass
            if foundaddress < 0:
                print('no devices found!')
            # successful quit:
            sys.exit(0)
        elif par == "-re":
            # readdress device
            oldaddress = int(sys.argv[2])
            # check humidity sensor:
            try:
                # intialize device
                instrument = SMSens(oldaddress,  2, '/dev/ttyUSB0', 9600)
                # try to read soil moisture
                h = instrument.read()
                # if no error happened, mark found device and exit loop
                print('device found at address ' + str(oldaddress) +
                      ' (response was ' + str(h) + ')')
            except:
                # cannot read from address, just continue with another:
                print('device not found at address ' + str(oldaddress))
                sys.exit(1)
            newaddress = int(sys.argv[3])
            if newaddress < 1 or newaddress > 247:
                print('incorrect new address value. ' +
                      'must be in interval [1,247]')
                # incorrect value, quit
                sys.exit(2)
            # check new address with user
            print('new address will be: ' + str(newaddress))
            yn = input('confirm yes/no:')
            if not yn == 'yes':
                print('not confirmed')
                # quit
                sys.exit(3)
            # readdress device
            instrument.readdress(newaddress)
            # try reading soil moisture at new address:
            h = instrument.read()
            print('response of device at new address was: ' + str(h))
            # successful quit:
            sys.exit(0)
        elif par == "-cont":
            try:
                # intialize device
                instrument = SMSens(int(sys.argv[2]),  2, '/dev/ttyUSB0', 9600)
                # continuously read:
                while True:
                    h = instrument.read()
                    print(str(h))
            except KeyboardInterrupt:
                pass
        else:
            print('unknown parameter')
            sys.exit(0)
