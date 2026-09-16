import json

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'r') as f:
    dashboard = json.load(f)

# Find the Raw Accelerometer panel
for panel in dashboard['panels']:
    if panel['title'] == "Raw Dynamic Accelerometer (X, Y, Z)":
        panel['title'] = "Grafik Seismogram Live (X, Y, Z)"
        panel['type'] = "timeseries"
        panel['fieldConfig'] = {
            "defaults": {
                "unit": "accMS2", # Acceleration m/s^2
                "custom": {
                    "drawStyle": "line",
                    "lineInterpolation": "linear",
                    "lineWidth": 2,
                    "fillOpacity": 10,
                    "spanNulls": False
                }
            },
            "overrides": []
        }
        panel['options'] = {
            "legend": {
                "displayMode": "list",
                "placement": "bottom"
            },
            "tooltip": {
                "mode": "single"
            }
        }
        # Update SQL to ensure it is cleanly formatted
        panel['targets'][0]['rawSql'] = """
SELECT 
  time AS "time", 
  accel_x AS "Guncangan X (Timur-Barat)", 
  accel_y AS "Guncangan Y (Utara-Selatan)", 
  accel_z AS "Guncangan Z (Vertikal)"
FROM sensor_telemetry 
WHERE node_id IN ($node) AND time > NOW() - INTERVAL '15 minutes' 
ORDER BY time ASC
"""
        break

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'w') as f:
    json.dump(dashboard, f, indent=2)

print("Dashboard Updated")
