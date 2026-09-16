import json

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'r') as f:
    dashboard = json.load(f)

for panel in dashboard['panels']:
    if panel.get('title') in ['Actuator Valve Status', 'Firmware Version (OTA)']:
        panel['options']['reduceOptions']['values'] = True
        
        # Ensure textMode is removed so Grafana uses default auto mapping
        if 'textMode' in panel['options']:
            del panel['options']['textMode']

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'w') as f:
    json.dump(dashboard, f, indent=2)
