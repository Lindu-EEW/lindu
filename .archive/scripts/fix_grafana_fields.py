import json

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'r') as f:
    dashboard = json.load(f)

for panel in dashboard['panels']:
    if panel.get('title') in ['Actuator Valve Status', 'Firmware Version (OTA)']:
        if 'fields' in panel['options']['reduceOptions']:
            del panel['options']['reduceOptions']['fields']
        # Set textMode to value_and_name just in case? No, Physical Pose doesn't have it.
        if 'textMode' in panel['options']:
            del panel['options']['textMode']

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'w') as f:
    json.dump(dashboard, f, indent=2)
