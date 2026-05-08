#!/bin/bash
# Monitor ruuvi2mqtt container health and fix Bluetooth if needed
#
# This script checks if the container has restarted recently due to Bluetooth issues.
# If the container has restarted multiple times in a short period, it runs fix.sh
# to restart the host Bluetooth service.
#
# Add to crontab to run every 5 minutes:
# */5 * * * * /home/rpi/work/ruuvi2mqtt/monitor-and-fix.sh >> /tmp/ruuvi2mqtt-monitor.log 2>&1

CONTAINER_NAME="ruuvi2mqtt"
RESTART_THRESHOLD=3  # Number of restarts in the time window
TIME_WINDOW=300      # Time window in seconds (5 minutes)
LOG_FILE="/tmp/ruuvi2mqtt-monitor.log"

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

# Check if container exists
if ! docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    log "Container ${CONTAINER_NAME} not found. Exiting."
    exit 0
fi

# Get container start time
CONTAINER_STARTED=$(docker inspect -f '{{.State.StartedAt}}' ${CONTAINER_NAME} 2>/dev/null)
if [ -z "$CONTAINER_STARTED" ]; then
    log "Could not get container start time. Exiting."
    exit 1
fi

# Convert to epoch time
START_EPOCH=$(date -d "$CONTAINER_STARTED" +%s 2>/dev/null || date -j -f "%Y-%m-%dT%H:%M:%S" "$CONTAINER_STARTED" +%s 2>/dev/null)
CURRENT_EPOCH=$(date +%s)
UPTIME=$((CURRENT_EPOCH - START_EPOCH))

log "Container ${CONTAINER_NAME} uptime: ${UPTIME}s"

# Get restart count from Docker
RESTART_COUNT=$(docker inspect -f '{{.RestartCount}}' ${CONTAINER_NAME} 2>/dev/null)
log "Container restart count: ${RESTART_COUNT}"

# Check if container has been restarting frequently
# If uptime is very short and restart count is high, there's likely a Bluetooth issue
if [ "$UPTIME" -lt "$TIME_WINDOW" ] && [ "$RESTART_COUNT" -ge "$RESTART_THRESHOLD" ]; then
    log "WARNING: Container has restarted ${RESTART_COUNT} times in the last ${UPTIME}s"
    log "This indicates a Bluetooth issue. Running fix.sh..."

    cd /home/rpi/work/ruuvi2mqtt || exit 1
    ./fix.sh

    log "Fix applied. Bluetooth service restarted and container restarted."
    exit 0
fi

# Also check container logs for Bluetooth watchdog errors in the last few minutes
RECENT_ERRORS=$(docker logs --since 5m ${CONTAINER_NAME} 2>&1 | grep -c "Bluetooth watchdog.*Exiting for container restart" || true)

if [ "$RECENT_ERRORS" -ge 2 ]; then
    log "WARNING: Found ${RECENT_ERRORS} Bluetooth watchdog errors in the last 5 minutes"
    log "Running fix.sh to restart Bluetooth service..."

    cd /home/rpi/work/ruuvi2mqtt || exit 1
    ./fix.sh

    log "Fix applied. Bluetooth service restarted and container restarted."
    exit 0
fi

log "Container appears healthy. No action needed."
