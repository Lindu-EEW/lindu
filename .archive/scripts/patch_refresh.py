import json

# 1. Update docker-compose.yml
with open('prototype/grafana-stack/docker-compose.yml', 'r') as f:
    dc = f.read()

if "GF_DASHBOARDS_MIN_REFRESH_INTERVAL" not in dc:
    dc = dc.replace('- GF_AUTH_ANONYMOUS_ORG_ROLE=Admin', '- GF_AUTH_ANONYMOUS_ORG_ROLE=Admin\n      - GF_DASHBOARDS_MIN_REFRESH_INTERVAL=1s')
    with open('prototype/grafana-stack/docker-compose.yml', 'w') as f:
        f.write(dc)

# 2. Update seismic.json
with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'r') as f:
    dash = json.load(f)

dash['refresh'] = '1s'

if 'timepicker' not in dash:
    dash['timepicker'] = {}
    
if 'refresh_intervals' not in dash['timepicker']:
    dash['timepicker']['refresh_intervals'] = ["1s", "5s", "10s", "30s", "1m", "5m", "15m", "30m", "1h", "2h", "1d"]
else:
    intervals = dash['timepicker']['refresh_intervals']
    if "1s" not in intervals:
        intervals.insert(0, "1s")

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'w') as f:
    json.dump(dash, f, indent=2)

