import json

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'r') as f:
    dashboard = json.load(f)

for i, panel in enumerate(dashboard.get('panels', [])):
    print(f"Panel {i}: {panel.get('title')} (gridPos: {panel.get('gridPos')})")

