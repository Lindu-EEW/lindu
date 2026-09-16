import json

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'r') as f:
    dashboard = json.load(f)

for p in dashboard.get('panels', []):
    if p.get('type') == 'geomap':
        # Change basemap to OpenStreetMap which has no API key watermark
        p['options']['basemap'] = {
            "type": "osm",
            "name": "Layer 0"
        }

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'w') as f:
    json.dump(dashboard, f, indent=2)

