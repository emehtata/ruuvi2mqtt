#!/bin/sh
set -e

# Initialize settings.py if it doesn't exist in the data volume
if [ ! -f /data/settings.py ]; then
    echo "No settings.py found in /data, creating from available template..."
    # Prefer settings.py if it exists in the image, otherwise use example
    if [ -f /app/settings.py ]; then
        cp /app/settings.py /data/settings.py
        echo "Created /data/settings.py from settings.py"
    else
        cp /app/settings.py.example /data/settings.py
        echo "Created /data/settings.py from settings.py.example"
    fi
    echo "Configure via web UI at http://<host>:${WEBAPP_PORT:-5883}"
fi

# Use settings from data volume
ln -sf /data/settings.py /app/settings.py

# Start the Flask web application in the background
echo "Starting web interface on port ${WEBAPP_PORT:-5883}..."
cd /app/webapp && python3 app.py &

# Start the main ruuvi2mqtt application
echo "Starting ruuvi2mqtt..."
cd /app && python3 ruuvi2mqtt.py
