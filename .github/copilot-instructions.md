# Ruuvi2MQTT Copilot Instructions

## Project Overview
RuuviTag Bluetooth sensor to MQTT gateway with Home Assistant auto-discovery. Dual-process architecture: main scanner (`ruuvi2mqtt.py`) + Flask web UI (`webapp/app.py`). Runs in Docker with persistent volume storage.

## Architecture

### Two-Process Model
- **Main process** (`ruuvi2mqtt.py`): Async BLE scanner, publishes to MQTT, handles HA discovery
- **Web UI** (`webapp/app.py`): Flask app on port 5883 for broker/tag configuration
- Both share `settings.py` via Docker volume (`/data/settings.py` → `/app/settings.py`)
- Started together via `docker/entrypoint.sh`: webapp runs in background, main app in foreground

### Data Flow
1. RuuviTag BLE broadcasts → async scanner (`RuuviTagSensor.get_data_async()`)
2. MAC matched against `my_ruuvis` dict → friendly name lookup
3. MQTT publish to all brokers in `my_brokers` dict
4. HA discovery messages sent with `retain=True` on first detection and every hour
5. Web UI changes to `settings.py` are auto-reloaded by main process (imports are live)

### Key Components
- **Settings**: `settings.py` contains `my_brokers` (dict) and `my_ruuvis` (MAC→name mapping)
- **Discovery**: Auto-resent every `DISCOVERY_RESEND_INTERVAL` (3600s) and on MQTT reconnect/HA online message
- **Multi-broker**: Single message published to all configured brokers simultaneously via `CLIENTS` dict

## Development Workflows

### Docker Development
```bash
make build              # Build Alpine image (use DISTRO=debian for Debian)
make run                # Run with volume (creates ruuvi2mqtt-data volume)
make run_mount          # Dev mode: mount current dir as /app
make logs               # View container logs
make volume-backup      # Export settings.py to settings.py.backup
make volume-restore     # Import from settings.py.backup
```

### Versioning
```bash
make tag                # Create new tag: YYYY.M.D-1 (auto-increments patch)
make tag-push           # Push latest tag to remote
make version            # Show current branch and release tags
```
- Format: `year.month.day-patch` (e.g., `2026.1.13-1`, `2026.1.13-2`)
- Multiple tags per day increment patch number automatically
- Version displayed in logs and web UI (from `git describe --tags`)
- Apps use `__version__` via `get_version()` function

### Testing
```bash
make venv               # Create venv with dependencies
make test               # Run pytest with coverage (84% target)
```
- Tests use `unittest.mock` to patch MQTT clients and RuuviTag sensor
- All discovery messages must verify `retain=True` parameter

### Local Development
- Web UI: `cd webapp && python3 app.py` (requires `settings.py` in parent dir)
- Main app: `python3 ruuvi2mqtt.py` (use `-s` flag for single-value publishing mode)

## Code Conventions

### MQTT Publishing
- State topic: `home/{room}` with JSON payload containing all sensor values
- Discovery topic: `homeassistant/sensor/{room}_{sensor}/config`
- **CRITICAL**: All discovery messages MUST use `retain=True` to survive broker restarts
- Example: `client.publish(topic, json.dumps(payload), retain=True)`

### Bluetooth Handling
- Async preferred (`RuuviTagSensor.get_data_async()`), falls back to sync (`get_datas()`)
- Log warning if no data received for >300 seconds (Bluetooth connectivity issue)
- Requires privileged container with `NET_ADMIN` and `NET_RAW` capabilities

### Settings Format
```python
my_brokers = {
    "broker_name": {"host": "192.168.1.100", "port": 1883}
}
my_ruuvis = {
    "AA:BB:CC:DD:EE:FF": "location-name"  # Use lowercase with hyphens
}
```

### Logging
- Standard library `logging` with timestamp + level
- `INFO` for normal operation, `WARNING` for connectivity issues, `DEBUG` for sensor data
- Format: `%(asctime)s %(levelname)-8s %(message)s`

## Docker Specifics

### Volume Management
- Named volume `ruuvi2mqtt-data` stores `settings.py` persistently
- `entrypoint.sh` initializes from `settings.py.example` on first run
- Symlink `/data/settings.py` → `/app/settings.py` for shared access

### Required Permissions
- `--privileged` flag for Bluetooth access
- `--network=host` for BLE scanning and MQTT connectivity
- `-v /run/dbus:/run/dbus:ro` for DBus communication (Bluetooth stack)
- `NET_ADMIN` and `NET_RAW` capabilities for raw socket access

## Integration Points

### Home Assistant Discovery
- Subscribes to `homeassistant/status` to detect HA restarts
- On "online" message, calls `force_rediscovery()` to resend all configs
- Sensor classes: `temperature`, `humidity`, `pressure`, `voltage` (battery)

### Web UI API
- `GET /api/settings`: Returns current `my_brokers` and `my_ruuvis`
- `POST /api/brokers`: Add broker, writes to `settings.py`
- `POST /api/ruuvis`: Add tag mapping, writes to `settings.py`
- Network scanning: mDNS (`_mqtt._tcp.local.`) + port 1883 TCP scan

## Common Pitfalls
- Forgetting `retain=True` on discovery messages breaks HA after broker restart
- Web UI changes don't require container restart (settings reloaded dynamically)
- Bluetooth requires host network mode; bridge networking won't work
- Test coverage checks `retain=True` on all discovery publishes (see `test_ruuvi2mqtt.py`)
