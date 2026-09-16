import json

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'r') as f:
    dashboard = json.load(f)

for panel in dashboard.get('panels', []):
    if 'Log Gempa' in panel.get('title', ''):
        for target in panel.get('targets', []):
            if 'rawSql' in target:
                target['rawSql'] = 'SELECT time_alert AS "Waktu Gempa (UTC)", magnitude AS "Magnitudo", radius_km AS "Radius Terdampak (km)", description AS "Detail Analisis" FROM tb_system_alerts ORDER BY time_alert DESC LIMIT 10'

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'w') as f:
    json.dump(dashboard, f, indent=2)

