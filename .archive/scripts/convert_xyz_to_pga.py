import json

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'r') as f:
    dashboard = json.load(f)

for panel in dashboard['panels']:
    if panel['title'] == "Grafik Seismogram Live (X, Y, Z)":
        panel['title'] = "Grafik Seismogram Live (Total Guncangan 3D)"
        panel['fieldConfig']['defaults']['unit'] = 'g' # Unit G-Force
        panel['targets'][0]['rawSql'] = """
SELECT 
  time AS "time", 
  node_id AS "metric",
  pga AS "Total Guncangan (PGA)"
FROM sensor_telemetry 
WHERE node_id IN ($node) AND time > NOW() - INTERVAL '15 minutes' 
ORDER BY time ASC
"""
        break

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'w') as f:
    json.dump(dashboard, f, indent=2)

print("Dashboard Converted to Single Number (PGA)")
