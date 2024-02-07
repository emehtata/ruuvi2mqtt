#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import datetime
import paho.mqtt.client as mqtt
import json
import sys
import platform
from ruuvitag_sensor.ruuvi import RuuviTagSensor
from settings import brokers
from settings import ruuvis

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
    "temperature": "°C",
    "humidity": "%",
    "pressure": "hPa",
    "battery": "mV",
    "acceleration": "mG",
    "acceleration_x": "mG",
    "acceleration_y": "mG",
    "acceleration_z": "mG",
    "rssi": "dBm",
    "movement_counter": "times"
  }

  for s in sendvals:
    payload = {
      "device_class":f"{s}",
      "state_topic":f"home/{room}",
      "unit_of_measurement":f"{sendvals[s]}",
      "value_template": "{{ value_json."+s+" }}",
      "unique_id": f"ruuvi{jdata['mac']}{s}",
      "object_id": f"{room}_{s}",
      "friendly_name": f"{room} {s}",
      "device":{
        "identifiers":[
          f"{room}"
        ],
        "name": f"{room}",
        "manufacturer": "Ruuvi",
        "model": "Ruuvitag"
      }
    }
    topic = f"homeassistant/sensor/{room}_{s}/config"
    my_data=json.dumps(payload).replace("'", '"')
    logging.info(f"{topic}: {my_data}")
    for b in brokers:
      clients[b].publish(topic, my_data)

  return

def handle_data(found_data):
  now=datetime.datetime.now(tz=datetime.timezone.utc)
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

