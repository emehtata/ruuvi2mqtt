# Ruuvi2MQTT

## Intro
This python script reads RuuviTag sensors and sends specified data to MQTT broker(s) defined in settings.py (see settings.py.example).

## Home Assistant discovery
When a Tag is detected for the first time, program sends configuration message to broker and Home Assistant shall create the wanted sensors for its use.

To initialize the sensors again, remove and setup MQTT broker in Home Assistant and restart Ruuvi2MQTT.

## Usage
`make build` 
- Build Docker image
  
`make run`
- Run container
  
`make run_mount`
- Run container but mount current directory as /app. Helpful for development.
  
`make stop`
- Stop running container
  
`make start`
- Start stopped container
  
`make rm`
- Remove container

## TODO
- Send discover data periodically

## Known issues
- BUG: Do not set device class based on its sensor's name
