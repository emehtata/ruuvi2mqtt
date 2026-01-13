#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ruuvi2mqtt

RuuviTag to MQTT gateway. For people who do not want to use Home Assistant
Ruuvi integration but read the sensors data straight from MQTT broker.
"""

import asyncio
import logging
import datetime
import json
import sys
import platform
import subprocess
from paho.mqtt.client import Client
from paho.mqtt.enums import CallbackAPIVersion
from ruuvitag_sensor.ruuvi import RuuviTagSensor
from settings import my_brokers
from settings import my_ruuvis

def get_version():
    """Get version from git tags or return 'dev'."""
    try:
        version = subprocess.check_output(
            ['git', 'describe', '--tags', '--always'],
            stderr=subprocess.DEVNULL,
            text=True
        ).strip()
        return version
    except (subprocess.CalledProcessError, FileNotFoundError):
        return 'dev'

__version__ = get_version()

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S'
)

MYHOSTNAME = platform.node()
FOUND_RUUVIS = []
CLIENTS = {}
SEND_SINGLE_VALUES = False  # pylint: disable=invalid-name
LAST_DATA_TIME = {}
LAST_DISCOVERY_RESEND = None
DISCOVERY_RESEND_INTERVAL = 3600

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
    logging.info("%s: %s", topic, jdata[keyname])
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
        f"rssi_{MYHOSTNAME}": {"class": None, "unit": "dBm"},
        "movement_counter": {"class": None, "unit": "times"}
    }

    for sensor_key, sensor_data in sendvals.items():
        payload = {
            "state_topic": f"home/{room}",
            "unit_of_measurement": f"{sensor_data['unit']}",
            "value_template": "{{ value_json." + sensor_key + " }}",
            "unique_id": f"ruuvi{jdata['mac']}{sensor_key}",
            "object_id": f"{room}_{sensor_key}",
            "name": f"{sensor_key}",
            "device": {
                "identifiers": [
                    f"{room}"
                ],
                "name": f"{room}",
                "manufacturer": "Ruuvi",
                "model": "Ruuvitag"
            }
        }
        if sensor_data['class'] is not None:
            payload.update({"device_class": f"{sensor_data['class']}"})
        topic = f"homeassistant/sensor/{room}_{sensor_key}/config"
        my_data = json.dumps(payload).replace("'", '"')
        logging.info("%s: %s", topic, my_data)
        for broker in my_brokers:
            CLIENTS[broker].publish(topic, my_data, retain=True)

def handle_data(found_data):
    """Handle Ruuvi tag sensor data.

    Args:
        found_data (tuple): Tuple containing room identifier and sensor data.

    Returns:
        None
    """
    global LAST_DISCOVERY_RESEND
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    mac = found_data[0]

    # Track last data time for each sensor
    LAST_DATA_TIME[mac] = now

    # Periodic discovery resend (once per hour)
    time_since_last_discovery = (
        LAST_DISCOVERY_RESEND is None or
        (now - LAST_DISCOVERY_RESEND).total_seconds() > DISCOVERY_RESEND_INTERVAL
    )
    if time_since_last_discovery:
        logging.info(
            "Periodic discovery resend triggered (interval: %d seconds)",
            DISCOVERY_RESEND_INTERVAL
        )
        force_rediscovery()
        LAST_DISCOVERY_RESEND = now

    logging.debug(found_data)
    try:
        room = my_ruuvis[found_data[0]]
        if room not in FOUND_RUUVIS:
            publish_discovery_config(room, found_data)
            FOUND_RUUVIS.append(room)
    except KeyError as key_error:
        room = f"Ruuvi-{found_data[0].replace(':', '')}"
        if room not in FOUND_RUUVIS:
            logging.debug(key_error)
            logging.warning(
                "Not found %s. Using topic home/%s", found_data[0], room
            )
            with open("detected_ruuvis.txt", "a", encoding="utf-8") as file_handle:
                file_handle.write(f"{now.isoformat()} {room} {found_data}\n")
            publish_discovery_config(room, found_data)
            FOUND_RUUVIS.append(room)
    topic = "home/" + room
    logging.debug(room)
    jdata = found_data[1]
    jdata.update({"room": room})
    jdata.update({"client": MYHOSTNAME})
    jdata.update({"ts": now.timestamp()})
    jdata.update({"ts_iso": now.isoformat()})
    jdata.update({f"rssi_{MYHOSTNAME}": jdata['rssi']})
    my_data = json.dumps(jdata).replace("'", '"')
    logging.debug(my_data)
    for broker in my_brokers:
        CLIENTS[broker].publish(topic, my_data)
        if SEND_SINGLE_VALUES:
            for key in jdata:
                send_single(jdata, key, CLIENTS[broker])
    logging.debug("-" * 40)

def force_rediscovery():
    """Force re-sending of all discovery messages.

    Returns:
        None
    """
    global FOUND_RUUVIS
    logging.info("Forcing discovery resend for all %d sensors", len(FOUND_RUUVIS))
    FOUND_RUUVIS = []

def on_connect(client, userdata, flags, return_code, properties=None):
    """MQTT on_connect callback function.

    Args:
        client (mqtt.Client): The MQTT client.
        userdata: The user data.
        flags: Connection flags.
        return_code (int): Return code.

    Returns:
        None
    """
    global FOUND_RUUVIS

    logging.info("MQTT Connected to broker, return code: %s", return_code)
    logging.debug("%s %x %x", userdata, flags, properties)
    if return_code == 0:
        logging.info("MQTT Connection successful")
        result = client.subscribe("homeassistant/status")
        logging.info("Subscribed to homeassistant/status, result: %s", result)
        logging.info("Clearing discovery cache to force resend on reconnection")
        FOUND_RUUVIS = []
    else:
        logging.error("Bad MQTT connection, return code: %s", return_code)

def on_message(client, userdata, msg, properties=None):
    """MQTT on_message callback function.

    Args:
        client (mqtt.Client): The MQTT client.
        userdata: The user data.
        msg (mqtt.MQTTMessage): The received MQTT message.

    Returns:
        None
    """
    payload = msg.payload.decode()
    logging.info("Received MQTT message on topic %s: %s", msg.topic, payload)
    logging.debug("%s %s %s", client, userdata, properties)
    if payload == "online":
        logging.warning(
            "Home Assistant sent 'online' status - forcing discovery resend"
        )
        force_rediscovery()

def on_disconnect(client, userdata, flags, return_code, properties=None):
    """MQTT on_disconnect callback function.

    Args:
        client (mqtt.Client): The MQTT client.
        userdata: The user data.
        return_code (int): Return code.

    Returns:
        None
    """
    if return_code != 0:
        logging.error("Unexpected MQTT disconnection.")
    logging.debug("%s %s %s %s", client, flags, userdata, properties)


def connect_brokers(brokers):
    """Connect to MQTT brokers.

    Args:
        brokers (dict): Dictionary containing broker configurations.

    Returns:
        dict: Dictionary containing connected MQTT clients.
    """
    for broker in brokers:
        logging.info("Connecting Broker: %s %s", broker, brokers[broker])
        # CLIENTS[broker] = Client(f"{MYHOSTNAME}-ruuviclient")
        CLIENTS[broker] = Client(
            CallbackAPIVersion.VERSION2, f"{MYHOSTNAME}-ruuviclient"
        )
        CLIENTS[broker].on_connect = on_connect
        CLIENTS[broker].on_disconnect = on_disconnect
        CLIENTS[broker].on_message = on_message
        CLIENTS[broker].connect_async(
            brokers[broker]['host'], brokers[broker]['port'], 60
        )
        logging.info("Connection OK %s %s", CLIENTS[broker], brokers[broker])
        CLIENTS[broker].loop_start()
    return CLIENTS

async def main():
    """Main async function for Bluetooth scanning.

    Continuously scans for RuuviTag sensor data and processes it.
    Logs warnings if no data is received for extended periods.

    Returns:
        None
    """
    last_receive = datetime.datetime.now(tz=datetime.timezone.utc)
    logging.info("Starting async Bluetooth scanning...")
    async for found_data in RuuviTagSensor.get_data_async():
        now = datetime.datetime.now(tz=datetime.timezone.utc)
        time_since_last = (now - last_receive).total_seconds()

        if time_since_last > 300:  # 5 minutes without data
            logging.warning(
                "No Bluetooth data received for %.0f seconds - "
                "possible Bluetooth issue",
                time_since_last
            )

        logging.debug("MAC: %s", found_data[0])
        logging.debug("Data: %s", found_data[1])
        handle_data(found_data)
        last_receive = now

if __name__ == '__main__':
    logging.info("ruuvi2mqtt version %s", __version__)
    if len(sys.argv) > 1 and sys.argv[1] == '-s':
        SEND_SINGLE_VALUES = True  # pylint: disable=invalid-name
    connect_brokers(my_brokers)
    try:
        # RuuviTagSensor.get_data(handle_data)
        asyncio.run(main())
    except (RuntimeError, NotImplementedError) as exc:
        logging.warning("async not working, trying get_datas: %s", exc)
        RuuviTagSensor.get_datas(handle_data)
