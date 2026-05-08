# Bluetooth Monitoring and Auto-Fix

## Problem

From time to time, the Bluetooth stack on the host gets stuck and stops sending data to the MQTT broker. The container watchdog detects this and exits, but restarting the container alone doesn't fix the underlying Bluetooth issue on the host. The only fix is to restart the Bluetooth service on the host.

## Solution

### Automated Monitoring (Recommended)

The `monitor-and-fix.sh` script automatically detects when the container is repeatedly restarting due to Bluetooth issues and runs `fix.sh` to restart the host Bluetooth service.

#### Setup

1. Make the script executable:
   ```bash
   chmod +x /home/rpi/work/ruuvi2mqtt/monitor-and-fix.sh
   ```

2. Add to crontab to run every 5 minutes:
   ```bash
   crontab -e
   ```

   Add this line:
   ```
   */5 * * * * /home/rpi/work/ruuvi2mqtt/monitor-and-fix.sh >> /tmp/ruuvi2mqtt-monitor.log 2>&1
   ```

3. Check the log to see if it's working:
   ```bash
   tail -f /tmp/ruuvi2mqtt-monitor.log
   ```

### How It Works

The monitoring script checks two conditions:

1. **Restart Loop Detection**: If the container has restarted 3+ times within 5 minutes, it runs `fix.sh`
2. **Log Analysis**: If the container logs show 2+ "Bluetooth watchdog" errors in the last 5 minutes, it runs `fix.sh`

When either condition is met, the script:
1. Stops and removes the container
2. Restarts the Bluetooth service on the host (`sudo service bluetooth restart`)
3. Starts the container again

### Manual Fix

If you need to fix it manually, just run:
```bash
./fix.sh
```

## Container Watchdog

The container has a built-in watchdog that:
- Checks every 10 seconds if Bluetooth data is being received
- Exits with error code 1 if no data for 60 seconds
- Logs a warning at 30 seconds
- The container's `--restart=unless-stopped` policy causes it to restart automatically

## Troubleshooting

### Check if monitoring is working:
```bash
cat /tmp/ruuvi2mqtt-monitor.log
```

### Check container logs:
```bash
docker logs ruuvi2mqtt | tail -50
```

### Check container restart count:
```bash
docker inspect -f '{{.RestartCount}}' ruuvi2mqtt
```

### Test the monitor script manually:
```bash
/home/rpi/work/ruuvi2mqtt/monitor-and-fix.sh
```

### Check if cron job is set:
```bash
crontab -l | grep monitor-and-fix
```
