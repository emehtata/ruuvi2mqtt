# Ruuvi2MQTT Web Interface

Web-based configuration interface for the Ruuvi2MQTT gateway.

## Features

- **MQTT Broker Configuration**: Add, view, and delete MQTT broker connections
- **Network Scanning**: Automatically discover MQTT brokers on your local network
  - mDNS/Zeroconf discovery (detects brokers advertising via Bonjour/Avahi)
  - Network port scanning for MQTT (port 1883)
- **RuuviTag Management**: Configure MAC address to location name mappings
- **Real-time Updates**: Changes are saved immediately to `settings.py`
- **Responsive Design**: Works on desktop and mobile devices

## Installation

1. Install dependencies:
```bash
cd webapp
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Running

### Development Mode

```bash
source .venv/bin/activate
python app.py
```

The web interface will be available at `http://localhost:5883`

To use a different port, set the `WEBAPP_PORT` environment variable:
```bash
WEBAPP_PORT=8080 python app.py
```

### Production Mode

For production deployment, use a WSGI server like Gunicorn:

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5883 app:app
```

## API Endpoints

### Get Settings
- **GET** `/api/settings` - Retrieve current configuration

### Brokers
- **POST** `/api/brokers` - Add a new broker
  ```json
  {
    "name": "local",
    "host": "192.168.1.100",
    "port": 1883
  }
  ```
- **DELETE** `/api/brokers/<name>` - Delete a broker

### RuuviTags
- **POST** `/api/ruuvis` - Add a new RuuviTag mapping
  ```json
  {
    "mac": "AA:BB:CC:DD:EE:FF",
    "name": "living-room"
  }
  ```
- **DELETE** `/api/ruuvis/<mac>` - Delete a RuuviTag mapping

## Security Notes

⚠️ **Important**: This web interface has no authentication by default. For production use:

1. Add authentication (Flask-Login, Flask-HTTPAuth, etc.)
2. Use HTTPS/TLS
3. Set a strong `SECRET_KEY` environment variable
4. Restrict access via firewall or reverse proxy

## Docker Integration

To run the web interface alongside the main application, add it to the Docker setup or run it as a separate container.
