import json

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'r') as f:
    dashboard = json.load(f)

for p in dashboard.get('panels', []):
    if p.get('type') == 'geomap':
        # 1. FIX AUTO FOCUS (Fit to Data)
        p['options']['view'] = {
            "id": "fit" # This tells Grafana to dynamically calculate bounding box based on markers
        }
        
        # 2. FIX COLOR & SIZE (More vibrant, larger dots)
        for layer in p['options'].get('layers', []):
            layer['config']['size'] = {"fixed": 25} # Huge dots
            layer['config']['color'] = {
                "field": "metric",
                "fixed": "dark-green"
            }
            
        p['fieldConfig']['defaults']['thresholds']['steps'] = [
            {
              "color": "#FF2B2B", # Neon Red for Offline
              "value": None
            },
            {
              "color": "#00FF00", # Neon Green for Online
              "value": 1
            }
        ]

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'w') as f:
    json.dump(dashboard, f, indent=2)

