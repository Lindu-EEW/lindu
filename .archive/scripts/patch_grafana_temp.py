import json

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'r') as f:
    dashboard = json.load(f)

for p in dashboard.get('panels', []):
    if p.get('title') == 'Temperature (°C)':
        # Hapus min/max agar grafana auto-scale dan bisa menampilkan -127
        if 'min' in p['fieldConfig']['defaults']:
            del p['fieldConfig']['defaults']['min']
        if 'max' in p['fieldConfig']['defaults']:
            del p['fieldConfig']['defaults']['max']

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'w') as f:
    json.dump(dashboard, f, indent=2)
