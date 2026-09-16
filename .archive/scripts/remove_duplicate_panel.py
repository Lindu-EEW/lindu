import json

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'r') as f:
    dashboard = json.load(f)

# Filter out the old Firmware Version panel
original_count = len(dashboard['panels'])
dashboard['panels'] = [p for p in dashboard.get('panels', []) if p.get('title') != 'Firmware Version (OTA)']
new_count = len(dashboard['panels'])

if original_count != new_count:
    with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'w') as f:
        json.dump(dashboard, f, indent=2)
    print("Duplicate panel removed.")
else:
    print("Panel not found.")
