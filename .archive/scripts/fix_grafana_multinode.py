import json

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'r') as f:
    dashboard = json.load(f)

for panel in dashboard.get('panels', []):
    targets = panel.get('targets', [])
    for t in targets:
        sql = t.get('rawSql', '')
        # Add node_id if it's not already there and if the query is selecting from sensor_telemetry or sensor_status
        if 'SELECT time, ' in sql and 'node_id' not in sql:
            # We must inject node_id into the SELECT clause
            sql = sql.replace('SELECT time, ', 'SELECT time, node_id, ')
            t['rawSql'] = sql
        
        # We also want Grafana to graph things separately, so time_series natively handles a string column 'node_id' 
        # by creating separate lines for each unique value.

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'w') as f:
    json.dump(dashboard, f, indent=2)

