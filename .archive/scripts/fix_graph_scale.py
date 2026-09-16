import json

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'r') as f:
    dashboard = json.load(f)

for p in dashboard.get('panels', []):
    if p.get('title') == 'Barometric Pressure (hPa)':
        p['fieldConfig']['defaults']['min'] = 980
        p['fieldConfig']['defaults']['max'] = 1030
    elif p.get('title') == 'Temperature (°C)':
        p['fieldConfig']['defaults']['min'] = 15
        p['fieldConfig']['defaults']['max'] = 45

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'w') as f:
    json.dump(dashboard, f, indent=2)

