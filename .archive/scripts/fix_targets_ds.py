import json

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'r') as f:
    dashboard = json.load(f)

for panel in dashboard['panels']:
    if panel.get('title') in ['Actuator Valve Status', 'Firmware Version (OTA)']:
        if 'targets' in panel and len(panel['targets']) > 0:
            panel['targets'][0]['datasource'] = {
                "type": "grafana-postgresql-datasource",
                "uid": "lindu_pg"
            }

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'w') as f:
    json.dump(dashboard, f, indent=2)
