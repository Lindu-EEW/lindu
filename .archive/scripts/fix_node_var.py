import json

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'r') as f:
    dash = json.load(f)

for p in dash.get('panels', []):
    targets = p.get('targets', [])
    for t in targets:
        if 'rawSql' in t:
            t['rawSql'] = t['rawSql'].replace('($node)', '($node_id)')

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'w') as f:
    json.dump(dash, f, indent=2)

