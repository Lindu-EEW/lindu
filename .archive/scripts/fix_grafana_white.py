import json

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'r') as f:
    dashboard = json.load(f)

for panel in dashboard['panels']:
    if panel.get('title') in ['Actuator Valve Status', 'Firmware Version (OTA)']:
        panel['fieldConfig'] = {
            "defaults": {
                "color": {
                    "mode": "fixed",
                    "fixedColor": "white"
                },
                "custom": {
                    "align": "auto",
                    "displayMode": "color-text"
                }
            },
            "overrides": []
        }

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'w') as f:
    json.dump(dashboard, f, indent=2)
