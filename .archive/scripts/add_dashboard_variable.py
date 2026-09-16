import json

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'r') as f:
    dashboard = json.load(f)

# 1. Add Templating (Dashboard Variable)
if 'templating' not in dashboard:
    dashboard['templating'] = {"list": []}

variable = {
  "name": "node",
  "type": "query",
  "datasource": {
    "type": "grafana-postgresql-datasource",
    "uid": "lindu_pg"
  },
  "query": "SELECT DISTINCT node_id FROM sensor_telemetry",
  "refresh": 1, 
  "sort": 1,
  "multi": True,
  "includeAll": True,
  "allValue": None
}

# Replace or insert
existing = [v for v in dashboard['templating']['list'] if v['name'] == 'node']
if not existing:
    dashboard['templating']['list'].append(variable)
else:
    dashboard['templating']['list'][0] = variable

# 2. Patch all queries to filter by $node
for panel in dashboard.get('panels', []):
    for t in panel.get('targets', []):
        sql = t.get('rawSql', '')
        if 'WHERE time' in sql and 'AND node_id IN' not in sql:
            # Inject the node filter
            sql = sql.replace("WHERE time", "WHERE node_id IN ($node) AND time")
            t['rawSql'] = sql

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'w') as f:
    json.dump(dashboard, f, indent=2)

