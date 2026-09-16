import json

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'r') as f:
    dashboard = json.load(f)

print(json.dumps(dashboard['panels'][1], indent=2))
