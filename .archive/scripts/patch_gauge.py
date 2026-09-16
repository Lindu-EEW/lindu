import json

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'r') as f:
    dash = json.load(f)

for p in dash.get('panels', []):
    if p.get('id') == 20: # PGA Terkini Gauge
        p['targets'][0]['rawSql'] = "SELECT CASE WHEN NOW() - ts > INTERVAL '15 seconds' THEN 0 ELSE pga END AS \"PGA\" FROM tb_sensor_telemetry ORDER BY ts DESC LIMIT 1"
        
with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'w') as f:
    json.dump(dash, f, indent=2)

