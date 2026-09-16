import json

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'r') as f:
    dashboard = json.load(f)

for panel in dashboard['panels']:
    if panel.get('title') in ['Actuator Valve Status', 'Firmware Version (OTA)']:
        # Wipe options completely and replace with just reduceOptions
        panel['options'] = {
            "reduceOptions": {
                "values": True,
                "calcs": ["lastNotNull"]
            }
        }
        # Remove fieldConfig
        if 'fieldConfig' in panel:
            del panel['fieldConfig']
        
        # Ensure targets exactly match Physical Pose
        if len(panel.get('targets', [])) > 0:
            if 'rawQuery' in panel['targets'][0]:
                del panel['targets'][0]['rawQuery']

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'w') as f:
    json.dump(dashboard, f, indent=2)
