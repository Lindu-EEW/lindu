import json

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'r') as f:
    dashboard = json.load(f)

new_panel = {
    "type": "stat",
    "title": "Actuator Valve Status",
    "gridPos": {
        "h": 4,
        "w": 4,
        "x": 20,
        "y": 14
    },
    "datasource": "PostgreSQL",
    "targets": [
        {
            "format": "table",
            "rawQuery": True,
            "rawSql": "SELECT node_id, valve_status FROM sensor_telemetry WHERE time >= NOW() - INTERVAL '1 minute' AND valve_status IS NOT NULL ORDER BY time DESC LIMIT 1;",
            "refId": "A"
        }
    ],
    "options": {
        "colorMode": "background",
        "justifyMode": "auto",
        "orientation": "auto",
        "reduceOptions": {
            "calcs": ["lastNotNull"],
            "fields": "",
            "values": False
        },
        "textMode": "auto"
    },
    "fieldConfig": {
        "defaults": {
            "color": {
                "mode": "thresholds"
            },
            "mappings": [
                {
                    "options": {
                        "ENABLED": { "color": "green", "index": 0, "text": "OPEN (Enabled)" },
                        "DISABLED": { "color": "red", "index": 1, "text": "CLOSED (Disabled)" }
                    },
                    "type": "value"
                }
            ],
            "thresholds": {
                "mode": "absolute",
                "steps": [
                    { "color": "green", "value": None }
                ]
            }
        },
        "overrides": []
    }
}

dashboard['panels'].append(new_panel)

# Fix IDs
for i, panel in enumerate(dashboard['panels']):
    panel['id'] = i + 1

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'w') as f:
    json.dump(dashboard, f, indent=2)

