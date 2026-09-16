import json

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'r') as f:
    dashboard = json.load(f)

# Update the Seismogram Panel to handle multiple nodes cleanly
for panel in dashboard['panels']:
    if panel['title'] == "Grafik Seismogram Live (X, Y, Z)":
        panel['targets'][0]['rawSql'] = """
SELECT 
  time AS "time", 
  node_id AS "metric",
  accel_x AS "X (Timur-Barat)", 
  accel_y AS "Y (Utara-Selatan)", 
  accel_z AS "Z (Vertikal)"
FROM sensor_telemetry 
WHERE node_id IN ($node) AND time > NOW() - INTERVAL '15 minutes' 
ORDER BY time ASC
"""
        break

# Let's also add a System Alerts (Consensus) Table Panel
alert_panel = {
  "type": "table",
  "title": "🚨 Log Gempa Tervalidasi (Sistem Konsensus Multi-Node)",
  "gridPos": {
    "h": 6,
    "w": 24,
    "x": 0,
    "y": 24
  },
  "targets": [
    {
      "refId": "A",
      "rawSql": "SELECT time AS \"Waktu Gempa\", magnitude AS \"Magnitudo\", radius_km AS \"Radius Terdampak (km)\", description AS \"Detail Analisis\" FROM tb_system_alerts ORDER BY time DESC LIMIT 10",
      "format": "table",
      "datasource": {
        "type": "grafana-postgresql-datasource",
        "uid": "lindu_pg"
      }
    }
  ],
  "datasource": {
    "type": "grafana-postgresql-datasource",
    "uid": "lindu_pg"
  }
}
dashboard['panels'].append(alert_panel)

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'w') as f:
    json.dump(dashboard, f, indent=2)

print("Dashboard Multi-Node & Consensus Patched")
