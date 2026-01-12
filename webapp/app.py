#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Ruuvi2MQTT Web Configuration Interface

A Flask web application for configuring RuuviTag MQTT gateway settings.
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for
import json
import os
import sys

# Add parent directory to path to import settings
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

SETTINGS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'settings.py')
SETTINGS_EXAMPLE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'settings.py.example')


def load_settings():
    """Load current settings from settings.py file."""
    settings = {
        'brokers': {},
        'ruuvis': {}
    }

    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r') as f:
                content = f.read()
                # Execute the settings file to get the dictionaries
                exec_globals = {}
                exec(content, exec_globals)
                settings['brokers'] = exec_globals.get('my_brokers', {})
                settings['ruuvis'] = exec_globals.get('my_ruuvis', {})
        except Exception as e:
            print(f"Error loading settings: {e}")
    elif os.path.exists(SETTINGS_EXAMPLE):
        # If settings.py doesn't exist, load from example
        try:
            with open(SETTINGS_EXAMPLE, 'r') as f:
                content = f.read()
                exec_globals = {}
                exec(content, exec_globals)
                settings['brokers'] = exec_globals.get('my_brokers', {})
                settings['ruuvis'] = exec_globals.get('my_ruuvis', {})
        except Exception as e:
            print(f"Error loading example settings: {e}")

    return settings


def save_settings(brokers, ruuvis):
    """Save settings to settings.py file."""
    try:
        with open(SETTINGS_FILE, 'w') as f:
            f.write("my_brokers = ")
            f.write(json.dumps(brokers, indent=2))
            f.write("\n\n")
            f.write("my_ruuvis = ")
            f.write(json.dumps(ruuvis, indent=2))
            f.write("\n")
        return True
    except Exception as e:
        print(f"Error saving settings: {e}")
        return False


@app.route('/')
def index():
    """Main page showing current configuration."""
    settings = load_settings()
    return render_template('index.html',
                          brokers=settings['brokers'],
                          ruuvis=settings['ruuvis'])


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
        else:
            return jsonify({'success': False, 'message': 'Error saving settings'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


@app.route('/api/brokers', methods=['POST'])
def add_broker():
    """Add a new MQTT broker."""
    try:
        settings = load_settings()
        data = request.get_json()

        name = data.get('name')
        host = data.get('host')
        port = data.get('port', 1883)

        if not name or not host:
            return jsonify({'success': False, 'message': 'Name and host are required'}), 400

        settings['brokers'][name] = {'host': host, 'port': int(port)}

        if save_settings(settings['brokers'], settings['ruuvis']):
            return jsonify({'success': True, 'message': 'Broker added successfully'})
        else:
            return jsonify({'success': False, 'message': 'Error saving broker'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


@app.route('/api/brokers/<name>', methods=['DELETE'])
def delete_broker(name):
    """Delete an MQTT broker."""
    try:
        settings = load_settings()

        if name in settings['brokers']:
            del settings['brokers'][name]
            if save_settings(settings['brokers'], settings['ruuvis']):
                return jsonify({'success': True, 'message': 'Broker deleted successfully'})
            else:
                return jsonify({'success': False, 'message': 'Error saving settings'}), 500
        else:
            return jsonify({'success': False, 'message': 'Broker not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


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
        else:
            return jsonify({'success': False, 'message': 'Error saving RuuviTag'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


@app.route('/api/ruuvis/<mac>', methods=['DELETE'])
def delete_ruuvi(mac):
    """Delete a RuuviTag mapping."""
    try:
        settings = load_settings()

        if mac in settings['ruuvis']:
            del settings['ruuvis'][mac]
            if save_settings(settings['brokers'], settings['ruuvis']):
                return jsonify({'success': True, 'message': 'RuuviTag deleted successfully'})
            else:
                return jsonify({'success': False, 'message': 'Error saving settings'}), 500
        else:
            return jsonify({'success': False, 'message': 'RuuviTag not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


if __name__ == '__main__':
    port = int(os.environ.get('WEBAPP_PORT', 5883))
    app.run(host='0.0.0.0', port=port, debug=True)
