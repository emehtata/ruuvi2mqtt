#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ruuvi2mqtt

RuuviTag to MQTT gateway. For people who do not want to use Home Assistant Ruuvi integration but read the sensors data straight from MQTT broker.
"""

import asyncio
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
    datefmt='%Y-%m-%d %H:%M:%S'
)

myhostname = platform.node()
found_ruuvis = []
clients = {}
send_single_values = False

def send_single(jdata, keyname, client):
    """Send a single sensor value to the MQTT broker.

    Args:
        jdata (dict): The data dictionary containing sensor values.
        keyname (str): The key corresponding to the sensor value to be sent.
        client (mqtt.Client): The MQTT client.

    Returns:
        None
    """
    topic = f"{jdata['room']}/{keyname}"
    logging.info(f"{topic}: {jdata[keyname]}")
    client.publish(topic, jdata[keyname])

def publish_discovery_config(room, found_data):
    """Publish discovery configuration to Home Assistant.

    Args:
        room (str): The room identifier.
        found_data (tuple): Tuple containing room identifier and sensor data.

    Returns:
        None
    """
    jdata = found_data[1]
    sendvals = {
        "temperature": {"class": "temperature", "unit": "°C"},
        "humidity": {"class": "humidity", "unit": "%"},
        "pressure": {"class": "pressure", "unit": "hPa"},
        "battery": {"class": "voltage", "unit": "mV"},
        "acceleration": {"class": None, "unit": "mG"},
        "acceleration_x": {"class": None, "unit": "mG"},
        "acceleration_y": {"class": None, "unit": "mG"},
        "acceleration_z": {"class": None, "unit": "mG"},
        f"rssi_{myhostname}": {"class": None, "unit": "dBm"},
        "movement_counter": {"class": None, "unit": "times"}
    }

    for s in sendvals:
        payload = {
            "state_topic": f"home/{room}",
            "unit_of_measurement": f"{sendvals[s]['unit']}",
            "value_template": "{{ value_json." + s + " }}",
            "unique_id": f"ruuvi{jdata['mac']}{s}",
            "object_id": f"{room}_{s}",
            "name": f"{s}",
            "device": {
                "identifiers": [
                    f"{room}"
                ],
                "name": f"{room}",
                "manufacturer": "Ruuvi",
                "model": "Ruuvitag"
            }
        }
        if sendvals[s]['class'] is not None:
            payload.update({"device_class": f"{sendvals[s]['class']}"})
        topic = f"homeassistant/sensor/{room}_{s}/config"
        my_data = json.dumps(payload).replace("'", '"')
        logging.info(f"{topic}: {my_data}")
        for b in brokers:
            clients[b].publish(topic, my_data)

def handle_data(found_data):
    """Handle Ruuvi tag sensor data.

    Args:
        found_data (tuple): Tuple containing room identifier and sensor data.

    Returns:
        None
    """
    global found_ruuvis
    now = datetime.datetime.now(tz=datetime.timezone.utc)

    logging.debug(found_data)
    try:
        room = ruuvis[found_data[0]]
        if room not in found_ruuvis:
            publish_discovery_config(room, found_data)
            found_ruuvis.append(room)
    except Exception as e:
        room = f"Ruuvi-{found_data[0].replace(':', '')}"
        if room not in found_ruuvis:
            logging.warning(f"Not found {found_data[0]}. Using topic home/{room}")
            with open(f"detected_ruuvis.txt", "a") as fp:
                fp.write(f"{now.isoformat()} {room} {found_data}\n")
            publish_discovery_config(room, found_data)
            found_ruuvis.append(room)
    topic = "home/" + room
    logging.debug(room)
    jdata = found_data[1]
    jdata.update({"room": room})
    jdata.update({"client": myhostname})
    jdata.update({"ts": now.timestamp()})
    jdata.update({"ts_iso": now.isoformat()})
    jdata.update({f"rssi_{myhostname}": jdata['rssi']})
    my_data = json.dumps(jdata).replace("'", '"')
    logging.debug(my_data)
    for b in brokers:
        clients[b].publish(topic, my_data)
        if send_single_values:
            for j in jdata:
                send_single(jdata, j, clients[b])
    logging.debug("-" * 40)

def on_connect(client, userdata, flags, rc, properties=None):
    """MQTT on_connect callback function.

    Args:
        client (mqtt.Client): The MQTT client.
        userdata: The user data.
        flags: Connection flags.
        rc (int): Return code.

    Returns:
        None
    """
    logging.info(f"Connected, returned code {rc}")
    if rc == 0:
        logging.info(f"Connected OK Returned code {rc}")
    else:
        logging.error(f"Bad connection Returned code {rc}")
    client.subscribe("homeassistant/status")

def on_message(client, userdata, msg, properties=None):
    """MQTT on_message callback function.

    Args:
        client (mqtt.Client): The MQTT client.
        userdata: The user data.
        msg (mqtt.MQTTMessage): The received MQTT message.

    Returns:
        None
    """
    global found_ruuvis
    payload = msg.payload.decode()
    logging.info(f"Received message on topic {msg.topic}: {payload}")
    if payload == "online":
        found_ruuvis = []

def on_disconnect(client, userdata, rc, properties=None):
    """MQTT on_disconnect callback function.

    Args:
        client (mqtt.Client): The MQTT client.
        userdata: The user data.
        rc (int): Return code.

    Returns:
        None
    """
    if rc != 0:
        logging.error("Unexpected MQTT disconnection.")

def connect_brokers(brokers):
    """Connect to MQTT brokers.

    Args:
        brokers (dict): Dictionary containing broker configurations.

    Returns:
        dict: Dictionary containing connected MQTT clients.
    """
    for b in brokers:
        logging.info(f"Connecting Broker: {b} {brokers[b]}")
        # clients[b] = mqtt.Client(f"{myhostname}-ruuviclient")
        clients[b] = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, f"{myhostname}-ruuviclient")
        clients[b].on_connect = on_connect
        clients[b].on_disconnect = on_disconnect
        clients[b].on_message = on_message
        clients[b].connect_async(brokers[b]['host'], brokers[b]['port'], 60)
        logging.info(f"Connection OK {clients[b]} {brokers[b]}")
        clients[b].loop_start()
    return clients

async def main():
    async for found_data in RuuviTagSensor.get_data_async():
        logging.debug(f"MAC: {found_data[0]}")
        logging.debug(f"Data: {found_data[1]}")
        handle_data(found_data)

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '-s':
        send_single_values = True
    clients = connect_brokers(brokers)
    try:
        # RuuviTagSensor.get_data(handle_data)
        asyncio.run(main())
    except Exception as e:
        logging.warning(f"async not working, trying get_datas: {e}")
        RuuviTagSensor.get_datas(handle_data)
