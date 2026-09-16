import json

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'r') as f:
    dash = json.load(f)

for p in dash.get('panels', []):
    if p.get('title') == "🖥️ Raspberry Pi (Server Health)":
        p['title'] = "🖥️ Lindu Backend (Host Health)"

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'w') as f:
    json.dump(dash, f, indent=2)

