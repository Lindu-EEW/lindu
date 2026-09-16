import json

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'r') as f:
    dashboard = json.load(f)

for panel in dashboard['panels']:
    if panel['title'] == "PGA & RMS Energy":
        panel['title'] = "Rasio Validasi Gempa (STA / LTA)"
        panel['fieldConfig']['defaults']['unit'] = 'none' # STA/LTA is a ratio, no unit
        panel['targets'][0]['rawSql'] = """
SELECT 
  time AS "time", 
  node_id AS "metric",
  rms AS "STA/LTA Ratio" 
FROM sensor_telemetry 
WHERE node_id IN ($node) AND time > NOW() - INTERVAL '15 minutes' 
ORDER BY time ASC
"""
        break

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'w') as f:
    json.dump(dashboard, f, indent=2)

print("Panel 2 Converted to STA/LTA")
