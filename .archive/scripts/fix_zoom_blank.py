import json

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'r') as f:
    dashboard = json.load(f)

for p in dashboard.get('panels', []):
    if p.get('type') == 'geomap':
        # Ubah view kembali ke manual zoom (zoom 10) di koordinat Tokyo
        # Kemungkinan 'fit' membuat zoom level terlalu dalam (zoom 20+) sehingga tile tidak ada dan blank
        p['options']['view'] = {
            "id": "zero",
            "lat": 35.6,
            "lon": 139.6,
            "zoom": 10
        }

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'w') as f:
    json.dump(dashboard, f, indent=2)

