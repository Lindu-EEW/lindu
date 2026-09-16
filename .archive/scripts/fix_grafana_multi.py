import json

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'r') as f:
    dash = json.load(f)

# 1. Update the variable to be multi-select so Grafana quotes the strings in IN () clauses
if 'templating' in dash and 'list' in dash['templating']:
    for var in dash['templating']['list']:
        if var.get('name') == 'node_id':
            var['multi'] = True
            var['includeAll'] = True
            if 'allValue' in var:
                del var['allValue'] # Let Grafana auto-expand to all values

# 2. Fix the Javascript in Command Center to handle arrays/multiple selections gracefully
for p in dash.get('panels', []):
    if p.get('id') == 13: # Command Center
        content = p['options']['content']
        # We need to make sure ${node_id:raw} doesn't break JS syntax if it has quotes.
        # Grafana replaces ${node_id:raw} with the raw string without quotes. If multiple, it's comma separated: node_1,node_2
        target_js = "let target = '${node_id:raw}';"
        replacement_js = "let target = '${node_id:raw}';\n    if (target.includes(',')) { target = 'all'; } // If multiple nodes selected, broadcast to all"
        
        if replacement_js not in content:
            content = content.replace(target_js, replacement_js)
            p['options']['content'] = content
        break

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'w') as f:
    json.dump(dash, f, indent=2)

