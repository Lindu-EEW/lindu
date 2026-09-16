import json
import copy

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'r') as f:
    dashboard = json.load(f)

panels = dashboard.get('panels', [])
new_panels = []

for panel in panels:
    if panel.get('title') and "Atmospheric" in panel['title']:
        # Create Temperature Panel
        temp_panel = copy.deepcopy(panel)
        temp_panel['title'] = "Temperature (°C)"
        temp_panel['gridPos']['w'] = 12
        temp_panel['gridPos']['x'] = 0
        temp_panel['targets'][0]['rawSql'] = "SELECT time, node_id, temperature AS \"Temperature (°C)\" FROM sensor_telemetry WHERE node_id IN ($node) AND time > NOW() - INTERVAL '15 minutes' AND temperature IS NOT NULL ORDER BY time ASC"
        temp_panel['fieldConfig']['overrides'] = []
        temp_panel['fieldConfig']['defaults']['unit'] = 'celsius'
        
        # Create Pressure Panel
        press_panel = copy.deepcopy(panel)
        press_panel['title'] = "Barometric Pressure (hPa)"
        press_panel['gridPos']['w'] = 12
        press_panel['gridPos']['x'] = 12
        press_panel['targets'][0]['rawSql'] = "SELECT time, node_id, pressure AS \"Pressure (hPa)\" FROM sensor_telemetry WHERE node_id IN ($node) AND time > NOW() - INTERVAL '15 minutes' AND pressure IS NOT NULL ORDER BY time ASC"
        press_panel['fieldConfig']['overrides'] = []
        press_panel['fieldConfig']['defaults']['unit'] = 'pressurehpa'
        
        new_panels.append(temp_panel)
        new_panels.append(press_panel)
    else:
        new_panels.append(panel)

# Reassign IDs sequentially to avoid conflicts
for i, p in enumerate(new_panels):
    p['id'] = i + 1

dashboard['panels'] = new_panels

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'w') as f:
    json.dump(dashboard, f, indent=2)

