# Ruuvi2MQTT

## Introduction
**Ruuvi2MQTT** is a gateway for sending RuuviTag sensor data to an MQTT broker. This application is designed for users who prefer not to use Home Assistant’s Ruuvi integration and want direct access to sensor data via MQTT.

## Pre-requisites

- **Network-connected computer with BLE support**

  - Tested with Raspberry Pi 2/3/4/5 and various x86 systems.
- **Linux distribution with Docker installed**

This Python script reads data from RuuviTag sensors and sends the specified information to one or more MQTT brokers as defined in settings.py (see settings.py.example for reference).

This python script reads RuuviTag sensors and sends specified data to MQTT broker(s) defined in **settings.py** (see *settings.py.example* for example).

## Home Assistant discovery
Upon detecting a new RuuviTag, the program automatically sends a configuration message to the broker, enabling Home Assistant to create sensors for easy integration.

To reinitialize sensors, either remove and re-add the MQTT broker in Home Assistant or restart Home Assistant. Discovery configuration resets whenever the MQTT client reconnects to the broker.

## Usage

Copy ```settings.example.py``` to ```settings.py``` and edit the brokers and ruuvis entries to match your setup.

**Note:** If no ```ruuvis``` key-values are specified, all RuuviTags will be named with the prefix "Ruuvi-" in MQTT data.

Use the following make commands for managing the Docker container:

- ```make build```

  Build the Docker image.

- ```make run```

  Run the container.

- ```make run_mount```

  Run the container with the current directory mounted as /app inside the container, useful for development.

- ```make stop```

  Stop the running container.

- ```make start```

  Start a previously stopped container.

- ```make rm```
  Remove the container.

If you prefer to use a Debian Slim image instead of Alpine, specify it with ```DISTRO=debian```, e.g., ```make DISTRO=debian build```.

Refer to the Makefile for additional rules and options.
