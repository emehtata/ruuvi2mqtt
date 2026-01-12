# Ruuvi2MQTT

## Introduction
**Ruuvi2MQTT** is a gateway for sending RuuviTag sensor data to an MQTT broker. This application is designed for users who prefer not to use Home Assistant’s Ruuvi integration and want direct access to sensor data via MQTT.

## Features

- **Automatic Home Assistant Discovery**: Automatically configures sensors in Home Assistant via MQTT discovery
- **Periodic Discovery Re-send**: Automatically re-sends discovery messages every hour to ensure reliability
- **Multiple MQTT Brokers**: Support for multiple MQTT brokers simultaneously
- **Bluetooth Monitoring**: Detects and warns about Bluetooth connection issues
- **Auto-detection**: Discovers unknown RuuviTags automatically
- **Docker Support**: Run in containers with Alpine or Debian base images

## Pre-requisites

- **Network-connected computer with BLE support**
  - Tested with Raspberry Pi 2/3/4/5 and various x86 systems
- **Linux distribution with Docker installed**

This Python script reads data from RuuviTag sensors and sends the specified information to one or more MQTT brokers as defined in `settings.py` (see `settings.py.example` for reference).

## Home Assistant Discovery

Upon detecting a new RuuviTag, the program automatically sends a configuration message to the broker, enabling Home Assistant to create sensors for easy integration.

**Discovery message behavior:**
- Initial discovery messages are sent when a new RuuviTag is detected
- Discovery messages are automatically re-sent every hour (configurable via `DISCOVERY_RESEND_INTERVAL`)
- Discovery messages are re-sent when the MQTT client reconnects to the broker
- Discovery messages are re-sent when Home Assistant sends an "online" status message

This ensures that sensors remain properly configured even after Home Assistant updates or restarts.

## Configuration

1. Copy `settings.example.py` to `settings.py`
2. Edit the `my_brokers` and `my_ruuvis` entries to match your setup

**Note:** If no `ruuvis` key-values are specified, all RuuviTags will be automatically named with the prefix "Ruuvi-" followed by their MAC address in MQTT data.

## Usage

### Docker Commands

Use the following make commands for managing the Docker container:

- `make build` - Build the Docker image
- `make run` - Run the container
- `make run_mount` - Run the container with the current directory mounted as /app (useful for development)
- `make stop` - Stop the running container
- `make start` - Start a previously stopped container
- `make restart` - Restart the container
- `make rm` - Remove the container
- `make logs` - View container logs
- `make push` - Build and push the image to a registry

**Image variants:**
If you prefer to use a Debian Slim image instead of Alpine, specify it with `DISTRO=debian`, e.g., `make DISTRO=debian build`.

### Development Commands

- `make venv` - Create a Python virtual environment
- `make test` - Run unit tests with coverage reporting (84% coverage)

### Registry Configuration

To push images to a custom registry, set the `REPOHOST` variable:
```bash
make build push REPOHOST=registry.example.com
```

Default: `localhost:5000`

## Testing

The project includes comprehensive unit tests covering:
- Home Assistant discovery message handling
- MQTT connection management
- Periodic discovery re-sending
- Bluetooth data tracking
- Unknown sensor auto-detection
- Multi-broker publishing

Run tests with:
```bash
make test
```

Test coverage: **84%** (17 tests)

## CI/CD

The project includes a Jenkins pipeline (`Jenkinsfile`) that:
1. Runs unit tests
2. Builds Docker images
3. Pushes to the configured registry

## Troubleshooting

### Bluetooth Issues

If the gateway stops receiving data:
1. Check container logs: `make logs`
2. The application will warn if no Bluetooth data has been received for 5 minutes
3. Restart Bluetooth service: `sudo service bluetooth restart`
4. Recreate container: `make rm && make run`

### Discovery Messages Not Appearing

If sensors don't appear in Home Assistant after an update:
1. Discovery messages are automatically re-sent hourly
2. Restart the container to force immediate re-send: `make restart`
3. Check Home Assistant MQTT integration status

## Additional Information

## Additional Information

Refer to the [Makefile](Makefile) for additional rules and options.
