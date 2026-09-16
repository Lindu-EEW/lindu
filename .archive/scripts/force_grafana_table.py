import json

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'r') as f:
    dashboard = json.load(f)

for panel in dashboard['panels']:
    if panel.get('title') in ['Actuator Valve Status', 'Firmware Version (OTA)']:
        panel['type'] = 'table'
        panel['options'] = {
            "showHeader": True
        }
        if 'reduceOptions' in panel:
            del panel['reduceOptions']

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'w') as f:
    json.dump(dashboard, f, indent=2)
