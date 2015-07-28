#!/bin/bash

# in /etc/modprobe.d/modules comment following lines:
# blacklist spi-bcm2708
# blacklist i2c-bcm2708
if grep -Fxq "spi-bcm2708" /etc/modprobe.d/raspi-blacklist.conf
then
        # ensure it is commented:
        sed -i 's/.*blacklist\s+spi-bcm2708.*/# blacklist spi-bcm2708/' /etc/modprobe.d/raspi-blacklist.conf
else
        echo "# blacklist spi-bcm2708" >> /etc/modprobe.d/raspi-blacklist.conf
fi
if grep -Fxq "i2c-bcm2708" /etc/modprobe.d/raspi-blacklist.conf
then
        # ensure it is commented:
        sed -i 'Ns/.*blacklist\s+i2c-bcm2708.*/# blacklist i2c-bcm2708/' /etc/modprobe.d/raspi-blacklist.conf
else
        echo "# blacklist i2c-bcm2708" >> /etc/modprobe.d/raspi-blacklist.conf
fi

# in /etc/modules add following lines:
# i2c-dev
# snd-bcm2835
if grep -Fxq "i2c-dev" /etc/modules
then
        # ensure it is not commented:
        sed -i 's/.*i2c-dev.*/i2c-dev/' /etc/modules
else
        echo i2c-dev >> /etc/modules
fi
if grep -Fxq "snd-bcm2835" /etc/modules
then
        # ensure it is not commented:
        sed -i 's/.*snd-bcm2835.*/snd-bcm2835/' /etc/modules
else
        echo snd-bcm2835 >> /etc/modules
fi

# install dependencies and requirements from web:
# is it really needed?:
apt-get install i2c-tools

apt-get install python-pip
apt-get install python-lxml
apt-get install python-webpy
pip install pygal
pip install arrow
# user install:
#pip install --user pygal
#pip install --user arrow

# enable autostart:
cp yawspisw /etc/init.d/yawspisw
chmod +x /etc/init.d/yawspisw
update-rc.d yawspi defaults
