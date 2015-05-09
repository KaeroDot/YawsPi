YAWSPI - Yet Another Watering System for raspberry PI
===================================================

General description
-------------------

System developed for watering of plants.

The watering system is built in such way that: there is one water source (e.g. barrel of water). A
pump is used to pump water from water source. Water is lead by tubes into several valves. From
valves water is lead to the water boxes. Control software always open only one valve, so it can
direct water from water source to the desired water box. Every water box and water source can have
one water level sensor of different types.

System can be set to water plants in water boxes in three different ways:
1, watering based on water level of the water box
2, watering based on the day of the week and hour of the day
3, watering every Nth day and hour.

The system logs watering and weather, so hopefully I will be able to relate temperature/humidity to
the water consumption of particular plants. The plan is also to increase or decrease frequency of
watering depending on the temperature/humidity/rain for the second and third mode of watering.

System consists of:
1. Hardware
  1. Controlling computer Raspberry Pi,
  2. power supply,
  3. water pump,
  4. water valves,
  5. YAWSPI electronics,
  6. water level sensors (optional),
  7. weather sensors (optional),
  8. water tubes.
2. Software with
  1. Hardware modules,
  2. hardware configuration,
  3. hardware abstraction layer,
  4. main program running in two threads, one is for watering, second one is for web server.

Detailed description of hardware
--------------------------------

### Raspberry Pi ###

System was built up on Raspberry Pi, but any other with general purpose input/output ports and able to run python can be used.

### Power supply ###

Raspberry Pi requires 5 V, water pump requires 6-9 V, water valves requires 24 V. Switching power
supply Mean Well RQ-85D was selected. It have one 5 V, 6 A output, one 12 V 2 A output, one 24 V 1 A
output and one -12 V 0.5 A output.
You can buy one in shops with electronics, like <http://www.gme.cz> or <http://www.farnell.com>.
![RQ-85D](./datasheets/power_source_Mean_Well_RQ-85D.jpg)

### Water pump ###

Immersible Barwig BW04 water pump was used. It can pump up to 10 l/min. For continuous usage needs 
6 to 9 V power source. It was immersed directly into the barrel - water reservoir.
You can buy it at e.g. <http://www.conrad.cz>.
![BW-04](./datasheets/water_pump_Barwig_BW04.jpg)

### Water valves ###

The cheapest water valve I was able to find was VIVA Sanela VE-RPE4115NC. It is monostable DC coil
powered by 24 V, normally closed (i.e. without any power it is closed). It is used in water
plumbing, so you can buy such valve in several shops, like: <http://www.sanela.cz/>.
![VE-RPE4115NC](VIVA_Sanela_VE-RPE4115NC.jpg)

### YAWSPI electronics ###

This is electronics to interface power source, water pump, water level and weather sensors to the
Raspberry Pi.

\todo{XXX}

### water level sensors ###
### weather sensors ###
### water tubes ###

Detailed description of software
--------------------------------

### hardware modules ###
### hardware configuration ###
### hardware abstraction layer ###
### main program ###
