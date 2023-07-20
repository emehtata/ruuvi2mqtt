#!/bin/bash -e

[ -f /etc/apt/apt.conf.d/99force-ipv4 ] || sudo echo "Acquire::ForceIPv4 "true";" > /etc/apt/apt.conf.d/99force-ipv4

sudo apt update
sudo apt upgrade

sudo apt install -y git mosquitto mosquitto-clients python3-pip bluez-hcidump bluetooth bluez blueman
sudo apt install -y libbz2-dev liblzma-dev libsqlite3-dev libncurses5-dev libgdbm-dev zlib1g-dev libreadline-dev libssl-dev tk-dev

sudo pip3 install --upgrade setuptools

sudo pip3 install ruuvitag-sensor
sudo pip3 install paho-mqtt

