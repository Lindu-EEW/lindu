import json

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'r') as f:
    dashboard = json.load(f)

new_panels = []
for panel in dashboard.get('panels', []):
    title = panel.get('title', '')
    if 'Live Seismic Map' not in title:
        new_panels.append(panel)

dashboard['panels'] = new_panels

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'w') as f:
    json.dump(dashboard, f, indent=2)

