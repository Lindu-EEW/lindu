import json

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'r') as f:
    dashboard = json.load(f)

for panel in dashboard['panels']:
    title = panel.get('title')
    
    if title == 'Firmware Version (OTA)':
        panel['gridPos'] = {"h": 6, "w": 12, "x": 0, "y": 20}
    
    elif title == 'Actuator Valve Status':
        panel['gridPos'] = {"h": 6, "w": 12, "x": 12, "y": 20}
        
    elif title == 'Current Tilt Angle':
        panel['gridPos'] = {"h": 8, "w": 8, "x": 0, "y": 26}
        
    elif title == 'Network Latency (ESP32 to MQTT)':
        panel['gridPos'] = {"h": 8, "w": 16, "x": 8, "y": 26}
        
    elif title == 'Physical Pose':
        panel['gridPos'] = {"h": 4, "w": 12, "x": 0, "y": 34}
        
    elif title == 'Hardware Health (I2C)':
        panel['gridPos'] = {"h": 4, "w": 12, "x": 12, "y": 34}
        
    elif title == '🚨 Log Gempa Tervalidasi (Sistem Konsensus Multi-Node)':
        panel['gridPos'] = {"h": 8, "w": 24, "x": 0, "y": 38}

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'w') as f:
    json.dump(dashboard, f, indent=2)
