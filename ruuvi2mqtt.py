#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import datetime
import paho.mqtt.client as mqtt
import json
import sys
import platform
import time
from ruuvitag_sensor.ruuvi import RuuviTagSensor
from settings import brokers
from settings import ruuvis

# Store current time for discovery updates
last_discovery=datetime.datetime.now(tz=datetime.timezone.utc)
DISCOVERY_INTERVAL=300

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')

myhostname=platform.node()

found_ruuvis = []

clients = {}

send_single_values = False

def send_single(jdata, keyname, client):
  topic=jdata['room']+f"/{keyname}"
  logging.info(f"{topic}: {jdata[keyname]}")
  client.publish(topic, jdata[keyname])

def publish_discovery_config(room, found_data):

  jdata = found_data[1]
  sendvals = {
    "temperature": { "class": "temperature", "unit": "°C" },
    "humidity": { "class": "humidity", "unit": "%" },
    "pressure": { "class": "pressure", "unit": "hPa" },
    "battery": { "class": "voltage", "unit": "mV" },
    "acceleration": { "class": None, "unit": "mG" },
    "acceleration_x": { "class": None, "unit": "mG" },
    "acceleration_y": { "class": None, "unit": "mG" },
    "acceleration_z": { "class": None, "unit": "mG" },
    "rssi": { "class": None, "unit": "dBm" },
    "movement_counter": { "class": None, "unit": "times" }
  }

  for s in sendvals:
    payload = {
      "state_topic":f"home/{room}",
      "unit_of_measurement":f"{sendvals[s]['unit']}",
      "value_template": "{{ value_json."+s+" }}",
      "unique_id": f"ruuvi{jdata['mac']}{s}",
      "object_id": f"{room}_{s}",
      "name": f"{room} {s}",
      "device":{
        "identifiers":[
          f"{room}"
        ],
        "name": f"{room}",
        "manufacturer": "Ruuvi",
        "model": "Ruuvitag"
      }
    }
    if sendvals[s]['class'] != None:
      payload.update( { "device_class": f"{sendvals[s]['class']}" } )
    topic = f"homeassistant/sensor/{room}_{s}/config"
    my_data=json.dumps(payload).replace("'", '"')
    logging.info(f"{topic}: {my_data}")
    for b in brokers:
      clients[b].publish(topic, my_data)

  return

def handle_data(found_data):
  global last_discovery
  global found_ruuvis
  now=datetime.datetime.now(tz=datetime.timezone.utc)
  if ( now.timestamp()-last_discovery.timestamp() > DISCOVERY_INTERVAL ):
    logging.info(f"DISCOVERY_INTERVAL ({DISCOVERY_INTERVAL}) s exceeded. Send new discovery.")
    last_discovery=now
    found_ruuvis={}
  else:
    logging.debug(f"{now.timestamp()-last_discovery.timestamp()} s from last discovery")

  logging.debug(found_data)
  try:
    room=ruuvis[found_data[0]]
    if not room in found_ruuvis:
      publish_discovery_config(room, found_data)
      found_ruuvis.append(room)
  except Exception as e:
    room=found_data[0].replace(':','')
    if not room in found_ruuvis:
      room=f"Ruuvi-{room}"
      logging.warning(f"Not found {found_data[0]}. Using topic home/{room}")
      with open(f"detected_ruuvis.txt", "a") as fp:
          fp.write(f"{now.isoformat()} {room}\n")
      publish_discovery_config(room, found_data)
      found_ruuvis.append(room)
  topic="home/"+room
  logging.debug(room)
  jdata=found_data[1]
  jdata.update( { "room": room } )
  jdata.update( { "client": myhostname } )
  jdata.update( { "ts": now.timestamp() } )
  jdata.update( { "ts_iso": now.isoformat() } )
  my_data=json.dumps(jdata).replace("'", '"')
  logging.debug(my_data)
  for b in brokers:
    clients[b].publish(topic, my_data)
    if send_single_values:
      for j in jdata:
        send_single(jdata, j, clients[b])
  logging.debug("-"*40)

def on_connect(client, userdata, flags, rc):
    logging.info(f"Connected, returned code {rc}")
    if rc==0:
        logging.info(f"Connected OK Returned code {rc}")
    else:
        logging.error(f"Bad connection Returned code {rc}")

def on_disconnect(client, userdata, rc):
    if rc != 0:
        logging.error("Unexpected MQTT disconnection.")

def on_publish(client, userdata, rc):
    logging.debug("Data published")

def connect_brokers(brokers):
  for b in brokers:
    logging.info(f"Connecting Broker: {b} {brokers[b]}")
    clients[b]=mqtt.Client(f"{myhostname}-ruuviclient")
    clients[b].on_connect = on_connect
    clients[b].on_publish = on_publish
    clients[b].on_disconnect = on_disconnect
    clients[b].connect_async(b, port=brokers[b]['port'])
    logging.info(f"Connection OK {clients[b]} {brokers[b]}")
    clients[b].loop_start()
  return clients

if __name__ == '__main__':
  if len(sys.argv) > 1 and sys.argv[1] == '-s':
    send_single_values = True
  clients=connect_brokers(brokers)
  try:
    RuuviTagSensor.get_data(handle_data)
  except Exception as e:
    logging.warning(f"get_data not working, trying get_datas: {e}")
    RuuviTagSensor.get_datas(handle_data)

