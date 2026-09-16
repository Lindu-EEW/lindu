import json

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'r') as f:
    dashboard = json.load(f)

for panel in dashboard['panels']:
    if panel.get('title') == 'Firmware Version (OTA)':
        panel['targets'][0]['rawSql'] = "SELECT DISTINCT ON (node_id) time, node_id, fw_version FROM sensor_status WHERE node_id IN ($node) AND time >= NOW() - INTERVAL '15 minutes' AND fw_version IS NOT NULL ORDER BY node_id, time DESC;"
    elif panel.get('title') == 'Actuator Valve Status':
        panel['targets'][0]['rawSql'] = "SELECT DISTINCT ON (node_id) time, node_id, valve_status FROM sensor_telemetry WHERE node_id IN ($node) AND time >= NOW() - INTERVAL '1 minute' AND valve_status IS NOT NULL ORDER BY node_id, time DESC;"

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'w') as f:
    json.dump(dashboard, f, indent=2)
