import json

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'r') as f:
    dashboard = json.load(f)

for panel in dashboard.get('panels', []):
    if 'Map' in panel.get('title', ''):
        # Fix SQL to ignore 0,0 nodes
        for target in panel['targets']:
            target['rawSql'] = "SELECT n.node_id as name, n.lat as latitude, n.lon as longitude, CASE WHEN s.status = 'offline' THEN 0 ELSE 1 END as metric FROM tb_nodes n LEFT JOIN LATERAL (SELECT status FROM sensor_status WHERE node_id = n.node_id ORDER BY time DESC LIMIT 1) s ON true WHERE n.lat != 0;"
        
        # Change basemap to default Grafana one
        panel['options']['basemap'] = {
            "type": "default",
            "name": "Layer 0"
        }

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'w') as f:
    json.dump(dashboard, f, indent=2)

