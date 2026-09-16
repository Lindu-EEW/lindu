import json

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'r') as f:
    dashboard = json.load(f)

for panel in dashboard.get('panels', []):
    targets = panel.get('targets', [])
    for t in targets:
        sql = t.get('rawSql', '')
        if 'LIMIT 1' in sql and 'sensor_status' in sql:
            # Change "SELECT time, node_id, ..." to "SELECT DISTINCT ON (node_id) time, node_id, ..."
            sql = sql.replace('SELECT time, node_id, ', 'SELECT DISTINCT ON (node_id) time, node_id, ')
            
            # Change "ORDER BY time DESC LIMIT 1" to "ORDER BY node_id, time DESC"
            sql = sql.replace('ORDER BY time DESC LIMIT 1', 'ORDER BY node_id, time DESC')
            t['rawSql'] = sql
            
            # For stat panels, we need to make sure options.reduceOptions.values is true or fields is 'all'
            # so it repeats the stat box for each node returned.
            if panel.get('type') == 'stat':
                if 'options' not in panel:
                    panel['options'] = {}
                if 'reduceOptions' not in panel['options']:
                    panel['options']['reduceOptions'] = {}
                panel['options']['reduceOptions']['values'] = True
                panel['options']['reduceOptions']['calcs'] = ['lastNotNull']

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'w') as f:
    json.dump(dashboard, f, indent=2)

