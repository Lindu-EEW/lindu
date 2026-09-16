import json

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'r') as f:
    dashboard = json.load(f)

new_panel = {
    "type": "stat",
    "title": "Firmware Version (OTA)",
    "gridPos": {
        "h": 4,
        "w": 4,
        "x": 20,
        "y": 18
    },
    "datasource": "PostgreSQL",
    "targets": [
        {
            "format": "table",
            "rawQuery": True,
            "rawSql": "SELECT DISTINCT ON (node_id) node_id, fw_version FROM sensor_status WHERE time >= NOW() - INTERVAL '15 minutes' AND fw_version IS NOT NULL ORDER BY node_id, time DESC;",
            "refId": "A"
        }
    ],
    "options": {
        "colorMode": "value",
        "justifyMode": "auto",
        "orientation": "auto",
        "reduceOptions": {
            "calcs": ["lastNotNull"],
            "fields": "",
            "values": False
        },
        "textMode": "value_and_name"
    },
    "fieldConfig": {
        "defaults": {
            "color": {
                "mode": "fixed",
                "fixedColor": "super-light-purple"
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
