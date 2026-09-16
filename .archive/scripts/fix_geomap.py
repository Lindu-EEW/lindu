import json

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'r') as f:
    dashboard = json.load(f)

for p in dashboard.get('panels', []):
    if p.get('type') == 'geomap':
        # Fix basemap to default (Grafana default, no API key needed usually)
        p['options']['basemap'] = {
            "type": "default",
            "name": "Layer 0"
        }
        
        # Fix location mapping so dots actually show up
        for layer in p['options'].get('layers', []):
            layer['location'] = {
                "mode": "coords",
                "latitude": "latitude",
                "longitude": "longitude"
            }
            
            # Make the dots a bit larger and clearer
            layer['config']['size'] = {"fixed": 12}

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'w') as f:
    json.dump(dashboard, f, indent=2)

