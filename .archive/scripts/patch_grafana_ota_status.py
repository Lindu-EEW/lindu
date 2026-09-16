import json

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'r') as f:
    dashboard = json.load(f)

for panel in dashboard['panels']:
    if panel.get('title') == 'Firmware Version (OTA)':
        # Modify the rawSql to include ota_status
        sql = panel['targets'][0]['rawSql']
        sql = sql.replace("fw_version FROM", "fw_version, ota_status FROM")
        panel['targets'][0]['rawSql'] = sql

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'w') as f:
    json.dump(dashboard, f, indent=2)
