import json

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'r') as f:
    dashboard = json.load(f)

for panel in dashboard['panels']:
    if panel.get('title') == 'Actuator Valve Status':
        panel['targets'][0]['rawSql'] = "SELECT DISTINCT ON (node_id) node_id, valve_status FROM sensor_telemetry WHERE time >= NOW() - INTERVAL '1 minute' AND valve_status IS NOT NULL ORDER BY node_id, time DESC;"
        # Make the stat panel show the node name as the title
        panel['options']['textMode'] = "value_and_name"

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'w') as f:
    json.dump(dashboard, f, indent=2)

