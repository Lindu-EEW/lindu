import json

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'r') as f:
    dashboard = json.load(f)

for panel in dashboard.get('panels', []):
    if panel.get('title') == 'Firmware Version (OTA)':
        for target in panel.get('targets', []):
            if 'rawSql' in target:
                target['rawSql'] = target['rawSql'].replace('fw_version, ota_status', 'fw_version, ota_status, status')
        
        # Tambahkan override field untuk mewarnai 'status'
        if 'fieldConfig' not in panel:
            panel['fieldConfig'] = {"defaults": {}, "overrides": []}
        
        if 'overrides' not in panel['fieldConfig']:
            panel['fieldConfig']['overrides'] = []
            
        panel['fieldConfig']['overrides'].append({
            "matcher": {
                "id": "byName",
                "options": "status"
            },
            "properties": [
                {
                    "id": "color",
                    "value": {
                        "mode": "fixed",
                        "fixedColor": "green"
                    }
                },
                {
                    "id": "mappings",
                    "value": [
                        {
                            "type": "value",
                            "options": {
                                "offline": {
                                    "color": "red",
                                    "index": 0,
                                    "text": "OFFLINE"
                                },
                                "online": {
                                    "color": "green",
                                    "index": 1,
                                    "text": "ONLINE"
                                }
                            }
                        }
                    ]
                }
            ]
        })

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'w') as f:
    json.dump(dashboard, f, indent=2)

