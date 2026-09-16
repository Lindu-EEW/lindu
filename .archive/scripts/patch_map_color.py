import json

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'r') as f:
    dashboard = json.load(f)

for panel in dashboard.get('panels', []):
    if 'Map' in panel.get('title', ''):
        # Change colors in thresholds
        panel['fieldConfig']['defaults']['thresholds']['steps'] = [
          {
            "color": "#8B0000", # Merah Pekat (Dark Red)
            "value": None
          },
          {
            "color": "#299c46", # Hijau Grafana
            "value": 1
          }
        ]

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'w') as f:
    json.dump(dashboard, f, indent=2)

