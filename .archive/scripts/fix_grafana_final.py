import json

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'r') as f:
    dashboard = json.load(f)

for panel in dashboard['panels']:
    title = panel.get('title')
    
    # 1. Fix Network Latency
    if title == 'Network Latency (ESP32 to MQTT)':
        panel['targets'][0]['rawSql'] = "SELECT time, node_id AS metric, latency_ms AS value FROM sensor_telemetry WHERE node_id IN ($node) AND time > NOW() - INTERVAL '15 minutes' AND latency_ms IS NOT NULL ORDER BY time ASC"

    # 2. Fix Hardware Health
    elif title == 'Hardware Health (I2C)':
        panel['targets'][0]['rawSql'] = "SELECT DISTINCT ON (node_id) time, node_id, sensor_ok::text FROM sensor_status WHERE node_id IN ($node) AND time > NOW() - INTERVAL '15 minutes' ORDER BY node_id, time DESC"
        panel['gridPos'] = {"h": 4, "w": 6, "x": 6, "y": 18} # Move to bottom row
        panel['options']['reduceOptions'] = {"values": True, "calcs": ["lastNotNull"]}

    # 3. Fix Physical Pose Layout
    elif title == 'Physical Pose':
        panel['gridPos'] = {"h": 4, "w": 6, "x": 0, "y": 18} # Bottom row

    # 4. Fix Actuator Valve Status
    elif title == 'Actuator Valve Status':
        panel['gridPos'] = {"h": 4, "w": 6, "x": 12, "y": 18} # Bottom row
        # Ensure it's a Stat panel again now that we know values:true works, or keep as table but bigger.
        # Let's keep it as table for safety, but make it look clean.
        panel['type'] = 'table'

    # 5. Fix Firmware Version
    elif title == 'Firmware Version (OTA)':
        panel['gridPos'] = {"h": 4, "w": 6, "x": 18, "y": 18} # Bottom row
        panel['type'] = 'table'


with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'w') as f:
    json.dump(dashboard, f, indent=2)
