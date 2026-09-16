import json

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'r') as f:
    dashboard = json.load(f)

for p in dashboard.get('panels', []):
    if p.get('type') == 'geomap':
        # Gunakan Custom URL untuk langsung menembak server tile OpenStreetMap
        p['options']['basemap'] = {
            "type": "custom",
            "config": {
                "url": "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
            },
            "name": "Layer 0"
        }

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'w') as f:
    json.dump(dashboard, f, indent=2)

