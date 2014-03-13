#=================================================================
# yawpi hardware configuration
#=================================================================

def yawpi_hw_config():

    # gv - 'global vars' - an empty module, used for storing vars (as
    # attributes), that need to be 'global' across threads and between
    # functions and classes:
    import gv

    # initialize dictionary with hardware settings:
    gv.hw = ({})

    # ------------------- Port Expander:
    # I2C address of port expander MCP23016 or MCP23017:
    gv.hw['PeAddress'] = 0x20

    # ------------------- Analog to Digital Converter:
    # XXX not used now:
    # # pin of the cable select for AD converter MCP3208 on the port expander:
    # gv.hw['AdcCableSelPin'] = 13

    # ------------------- Weather Sensors:
    gv.hw['SeTemp'] = 0     # temperature sensor present
    gv.hw['SeRain'] = 0     # rain sensor present
    gv.hw['SeHumid'] = 0    # humidity sensor present
    gv.hw['SePress'] = 0    # pressure sensor present

    # ------------------- Pump:
    gv.hw['PuPin'] = 0   # pin of pump relay connected to port expander
    gv.hw['PuSpeed'] = 0.1  # approx. flowrate of the pump in litres per second

    # ------------------- Stations:
    # number of watering stations (each one has at least one valve,
    # and usually one or more water level sensor):
    gv.hw['StNo'] = 1
    # water capacity of each station in litres:
    gv.hw['StCap'] = [0.5]
    # station name:
    gv.hw['StName'] = ['test']

    # ------------------- Water Level Sensors:
    # possible sensor types:
    #   none - no water level sensor, amount of water is determined by water
    #       capacity
    #   min - switch at the bottom of the water container of the station
    #       (detects container is empty)
    #   max- switch at the top the water container of the station
    #      (detects container is full)
    #   minmax - switch at the bottom and top of the station water container
    #      (detects container is empty and is full)
    #   grad - some analog sensor
    #
    # type of water level sensor:
    gv.hw['StWLSensorType'] = ['min']
    # pin of the water level sensor on the Port Expander or ADC:
    gv.hw['StWLSensorPin'] = [1]

    # Barrel:
    # reservoir of water:
    # water capacity of the barrel
    gv.hw['BaCap'] = 10
    # type of water level sensor:
    gv.hw['BaWLSensorType'] = ['min']
    # pins of the water level sensor of the barrel:
    gv.hw['BaWLSensorPin'] = [3]

    # Valves:
    # pins of valves of stations connected to port expander:
    gv.hw['StValvePin'] = [2]
