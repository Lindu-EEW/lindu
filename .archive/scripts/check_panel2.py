import json

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'r') as f:
    dashboard = json.load(f)

for panel in dashboard['panels']:
    if panel['title'] == "PGA & RMS Energy":
        print(panel['targets'][0]['rawSql'])
