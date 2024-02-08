# Ruuvi2MQTT

## Intro
RuuviTag to MQTT gateway. For people who do not want to use Home Assistant Ruuvi integration but read
the sensors data straight from MQTT broker.

## Pre-requisites

- A computer with network connection and BLE capability. Tested with Raspberry Pi 2/3/4/5 and several x86 computers.
- Linux distro with Docker installed

This python script reads RuuviTag sensors and sends specified data to MQTT broker(s) defined in **settings.py** (see *settings.py.example* for example).

## Home Assistant discovery
When a Tag is detected for the first time, program sends configuration message to broker and Home Assistant shall create the wanted sensors for its use.

To initialize the sensors again, remove and setup MQTT broker in Home Assistant and restart Ruuvi2MQTT.

## Usage

Copy settings.example.py to settings.py and edit *brokers* and *ruuvis* to match your environment.

Note: if you don't add any *ruuvis* key-values, all your RuuviTags will be named as Ruuvi-<mac> in MQTT data.

`make build` 
- Build Docker image

`make run`
- Run container

`make run_mount`
- Run container but mount current directory as /app in container. Helpful for development.

`make stop`
- Stop running container

`make start`
- Start stopped container

`make rm`
- Remove container

If you want to use Debian slim image instead of Alpine, use `make DISTRO=debian <rule>` e.g. `make DISTRO=debian build`

See **Makefile** for other rules.

## TODO
- Script version info

