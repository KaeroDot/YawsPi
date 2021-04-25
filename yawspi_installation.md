Installation of yawspisw on a fresh sd card
===
1. [download Jessie lite](https://www.raspberrypi.org/downloads/raspbian/)
1. check checksum
1. unzip
1. install according
[help](https://www.raspberrypi.org/documentation/installation/installing-images/linux.md)

        sudo dd bs=4M if=2016-05-27-raspbian-jessie-lite.img of=/dev/mmcblk0
1. sync:

        sync
1. put SD card into raspberry, connect ethernet, switch on power source, wait a little
1. find out ip address of rapsberry
1. login:

        ssh pi@ip.address.of.raspberry
1. run

        sudo raspi-config
    select *Advanced Options*, and expand the filesystem to whole image. reboot.
1. login, run raspi-config again, select *System Options* and set hostname to *yawspi*, select *Interface Options* and enable SPI and I2C, 
    select *Localisation Options* and select timezone.
1. install wicd (and remove dhcpcd5 to remove conflicts) for wifi:
    (debug for nonworking wpa_supplicant: ```sudo wpa_supplicant -c/etc/wpa_supplicant/wpa_supplicant.conf -iWIFIINTERFACE -d```)

        sudo apt update
        sudo apt purge dhcpcd5
        sudo apt install wicd-curses
    run wicd-curses and setup your wifi, disconnect ethernet and test wifi connection
1. set local time zone:

        sudo dpkg-reconfigure tzdata
1. copy ssh id:

        ssh-copy-id yawspi
1. copy keys to github
1. setup .ssh config:

        vi .ssh/config
    with content:

        Host github.com
        User git
        Hostname github.com
        PreferredAuthentications publickey
        IdentityFile /home/pi/.ssh/KEY_FILE_NAME
1. check github connection

        ssh -T git@github.com
1. install git:

        sudo apt install git
1. pull yawspi git:

        git clone git@github.com:KaeroDot/YawsPi.git
1. install yawspi dependencies:

        sudo apt install gnuplot-nox python3-pip python3-arrow python3-rpi.gpio python3-smbus
        pip3 install --user minimalmodbus
    webpy from repository can be outdated so it is better to install from pip:
        pip3 install --user webpy
1. cd to `YawsPi/yawspisw/`, edit `hw_config.py` according the hardware configuration
1. cd to `YawsPi/yawspisw/` and run following to check hardware is ok:

        python3 hw_control.py -all
1. cd to `YawsPi/yawspisw/` and run following to check everything is ok:

        python3 yawspisw.py 
1. copy `yawspisw.service` in `yawspisw` directory to `/lib/systemd/system`:

        sudo mv yawspi.service /lib/systemd/system
1. check that permissions are 644:

        sudo chmod 644 /lib/systemd/system/yawspi.service
1. reload daemons in systemd:

        sudo systemctl daemon-reload
1. enable the yawspi sservice:

        sudo systemctl enable yawspi.service
1. reboot and check yawspi is running:

        sudo reboot
1. there should be running yawspi webpage at [http://ip.address.of.raspberry:8080](http://ip.address.of.raspberry:8080)

Debug
===
Service running?

    sudo systemctl status yawspi.service
Available i2c devices?

    sudo i2cdetect -y 1
    sudo i2cdetect -l

Hardware working? First try:

    python hw_control.py -nowater
Then:

    python hw_control.py -all
Detailed testing:

    python
    hw = hw_control.YawspiHW()
    import hw_control
Water pump on/off:

    hw.so_switch(1)
    hw.so_switch(0)

Station `0` valve switch on/off:

    hw.st_switch(0, 1)
    hw.st_switch(0, 0)
