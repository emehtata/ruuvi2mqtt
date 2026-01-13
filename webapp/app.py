#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Ruuvi2MQTT Web Configuration Interface

A Flask web application for configuring RuuviTag MQTT gateway settings.
"""

import json
import os
import sys
import socket
import threading
import time

from flask import Flask, render_template, request, jsonify
from zeroconf import ServiceBrowser, ServiceListener, Zeroconf

# Add parent directory to path to import settings
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

SETTINGS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'settings.py')
SETTINGS_EXAMPLE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'settings.py.example')


class MQTTListener(ServiceListener):
    """Listener for mDNS MQTT service discovery."""

    def __init__(self):
        self.discovered_brokers = []

    def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        info = zc.get_service_info(type_, name)
        if info:
            # Get the first valid IPv4 address
            addresses = [socket.inet_ntoa(addr) for addr in info.addresses
                        if len(addr) == 4]
            if addresses:
                broker = {
                    'name': name.split('.')[0],
                    'host': addresses[0],
                    'port': info.port,
                    'type': 'mdns'
                }
                self.discovered_brokers.append(broker)

    def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        pass

    def update_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        pass


def scan_mqtt_brokers(timeout=5):  # pylint: disable=too-many-locals
    """Scan for MQTT brokers using mDNS and network scanning.

    Args:
        timeout (int): Scan timeout in seconds

    Returns:
        list: List of discovered MQTT brokers
    """
    discovered = []

    # mDNS/Zeroconf discovery
    try:
        zeroconf = Zeroconf()
        listener = MQTTListener()
        ServiceBrowser(zeroconf, "_mqtt._tcp.local.", listener)

        time.sleep(timeout)

        discovered.extend(listener.discovered_brokers)
        zeroconf.close()
    except (OSError, RuntimeError) as exc:
        print(f"mDNS discovery error: {exc}")

    # Network scan for common MQTT port on local subnet
    try:
        # Get actual network IP (not localhost)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # Connect to external address (doesn't actually send data)
            s.connect(('8.8.8.8', 80))
            local_ip = s.getsockname()[0]
        finally:
            s.close()

        subnet = '.'.join(local_ip.split('.')[:-1])
        print(f"Scanning subnet: {subnet}.0/24")

        # Scan a broader range including common server IPs
        common_ips = list(range(1, 255))  # Scan entire subnet

        def check_port(ip, mqtt_port=1883, timeout=0.3):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(timeout)
                result = sock.connect_ex((ip, mqtt_port))
                sock.close()
                return result == 0
            except (OSError, socket.error):
                return False

        results = []

        def scan_ip(last_octet):
            ip = f"{subnet}.{last_octet}"
            if check_port(ip):
                results.append({
                    'name': f'mqtt-{last_octet}',
                    'host': ip,
                    'port': 1883,
                    'type': 'scan'
                })

        threads = []
        for last_octet in common_ips:
            thread = threading.Thread(target=scan_ip, args=(last_octet,))
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()

        discovered.extend(results)
    except (OSError, socket.error) as exc:
        print(f"Network scan error: {exc}")

    # Remove None values and duplicates
    discovered = [b for b in discovered if b is not None]
    unique_brokers = []
    seen_hosts = set()

    for broker in discovered:
        if broker['host'] not in seen_hosts:
            seen_hosts.add(broker['host'])
            unique_brokers.append(broker)

    return unique_brokers


def load_settings():
    """Load current settings from settings.py file."""
    settings = {
        'brokers': {},
        'ruuvis': {}
    }

    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                content = f.read()
                # Execute the settings file to get the dictionaries
                exec_globals = {}
                exec(content, exec_globals)  # pylint: disable=exec-used
                settings['brokers'] = exec_globals.get('my_brokers', {})
                settings['ruuvis'] = exec_globals.get('my_ruuvis', {})
        except (OSError, SyntaxError) as exc:
            print(f"Error loading settings: {exc}")
    elif os.path.exists(SETTINGS_EXAMPLE):
        # If settings.py doesn't exist, load from example
        try:
            with open(SETTINGS_EXAMPLE, 'r', encoding='utf-8') as f:
                content = f.read()
                exec_globals = {}
                exec(content, exec_globals)  # pylint: disable=exec-used
                settings['brokers'] = exec_globals.get('my_brokers', {})
                settings['ruuvis'] = exec_globals.get('my_ruuvis', {})
        except (OSError, SyntaxError) as exc:
            print(f"Error loading example settings: {exc}")

    return settings


def save_settings(brokers, ruuvis):
    """Save settings to settings.py file."""
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            f.write("my_brokers = ")
            f.write(json.dumps(brokers, indent=2))
            f.write("\n\n")
            f.write("my_ruuvis = ")
            f.write(json.dumps(ruuvis, indent=2))
            f.write("\n")
        return True
    except OSError as exc:
        print(f"Error saving settings: {exc}")
        return False


@app.route('/')
def index():
    """Main page showing current configuration."""
    settings = load_settings()
    return render_template('index.html',
                          brokers=settings['brokers'],
                          ruuvis=settings['ruuvis'])


@app.route('/api/scan/mqtt', methods=['GET'])
def scan_mqtt():
    """API endpoint to scan for MQTT brokers."""
    try:
        timeout = int(request.args.get('timeout', 5))
        brokers = scan_mqtt_brokers(timeout)
        return jsonify({'success': True, 'brokers': brokers})
    except (ValueError, TypeError) as exc:
        return jsonify({'success': False, 'message': str(exc)}), 500


@app.route('/api/settings', methods=['GET'])
def get_settings():
    """API endpoint to get current settings."""
    settings = load_settings()
    return jsonify(settings)


@app.route('/api/settings', methods=['POST'])
def update_settings():
    """API endpoint to update settings."""
    try:
        data = request.get_json()
        brokers = data.get('brokers', {})
        ruuvis = data.get('ruuvis', {})

        if save_settings(brokers, ruuvis):
            return jsonify({'success': True, 'message': 'Settings saved successfully'})
        return jsonify({'success': False, 'message': 'Error saving settings'}), 500
    except (TypeError, AttributeError) as exc:
        return jsonify({'success': False, 'message': str(exc)}), 400


@app.route('/api/brokers', methods=['POST'])
def add_broker():
    """Add a new MQTT broker."""
    try:
        settings = load_settings()
        data = request.get_json()

        name = data.get('name')
        host = data.get('host')
        broker_port = data.get('port', 1883)

        if not name or not host:
            return jsonify({'success': False, 'message': 'Name and host are required'}), 400

        settings['brokers'][name] = {'host': host, 'port': int(broker_port)}

        if save_settings(settings['brokers'], settings['ruuvis']):
            return jsonify({'success': True, 'message': 'Broker added successfully'})
        return jsonify({'success': False, 'message': 'Error saving broker'}), 500
    except (TypeError, ValueError, AttributeError) as exc:
        return jsonify({'success': False, 'message': str(exc)}), 400


@app.route('/api/brokers/<name>', methods=['DELETE'])
def delete_broker(name):
    """Delete an MQTT broker."""
    try:
        settings = load_settings()

        if name in settings['brokers']:
            del settings['brokers'][name]
            if save_settings(settings['brokers'], settings['ruuvis']):
                return jsonify({'success': True, 'message': 'Broker deleted successfully'})
            return jsonify({'success': False, 'message': 'Error saving settings'}), 500
        return jsonify({'success': False, 'message': 'Broker not found'}), 404
    except (TypeError, KeyError) as exc:
        return jsonify({'success': False, 'message': str(exc)}), 400


@app.route('/api/ruuvis', methods=['POST'])
def add_ruuvi():
    """Add a new RuuviTag mapping."""
    try:
        settings = load_settings()
        data = request.get_json()

        mac = data.get('mac')
        name = data.get('name')

        if not mac or not name:
            return jsonify({'success': False, 'message': 'MAC address and name are required'}), 400

        settings['ruuvis'][mac] = name

        if save_settings(settings['brokers'], settings['ruuvis']):
            return jsonify({'success': True, 'message': 'RuuviTag added successfully'})
        return jsonify({'success': False, 'message': 'Error saving RuuviTag'}), 500
    except (TypeError, AttributeError) as exc:
        return jsonify({'success': False, 'message': str(exc)}), 400


@app.route('/api/ruuvis/<mac>', methods=['DELETE'])
def delete_ruuvi(mac):
    """Delete a RuuviTag mapping."""
    try:
        settings = load_settings()

        if mac in settings['ruuvis']:
            del settings['ruuvis'][mac]
            if save_settings(settings['brokers'], settings['ruuvis']):
                return jsonify({'success': True, 'message': 'RuuviTag deleted successfully'})
            return jsonify({'success': False, 'message': 'Error saving settings'}), 500
        return jsonify({'success': False, 'message': 'RuuviTag not found'}), 404
    except (TypeError, KeyError) as exc:
        return jsonify({'success': False, 'message': str(exc)}), 400


if __name__ == '__main__':
    port = int(os.environ.get('WEBAPP_PORT', 5883))
    app.run(host='0.0.0.0', port=port, debug=True)
