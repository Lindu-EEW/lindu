import json

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'r') as f:
    dashboard = json.load(f)

# Fix HTML to add the Reset Button
for p in dashboard.get('panels', []):
    if p.get('title') == 'Interactive Command Center':
        # Add Reset button
        if "sendCmd('factory_reset')" not in p['options']['content']:
            target_html = '''<button onclick="sendCmd('force_update')" style="background: #7aa2f7; color: #1a1b26; font-weight: bold; border: none; padding: 10px 15px; border-radius: 4px; cursor: pointer; flex: 1;"><i class="fa fa-download"></i> FORCE OTA UPDATE</button>'''
            replace_html = target_html + '''
  </div>
  <div style="display: flex; gap: 10px; margin-top: 10px; flex-wrap: wrap;">
    <button onclick="if(confirm('Yakin mereset WiFi & LongLat? Alat akan offline.')) sendCmd('factory_reset')" style="background: #f7768e; color: #ffffff; font-weight: bold; border: none; padding: 10px 15px; border-radius: 4px; cursor: pointer; flex: 1;"><i class="fa fa-warning"></i> FACTORY RESET NODE</button>'''
            p['options']['content'] = p['options']['content'].replace(target_html, replace_html)

# Let's cleanly set gridPos for all known panels to avoid overlap
layout_map = {
    "Active Nodes (Last 5 Min)": {"w": 4, "h": 5, "x": 0, "y": 0},
    "Interactive Command Center": {"w": 8, "h": 5, "x": 4, "y": 0}, # Lebarkan sikit
    "📡 Live Fleet Status (Online / Offline)": {"w": 12, "h": 5, "x": 12, "y": 0},
    
    "Grafik Seismogram Live (Total Guncangan 3D)": {"w": 12, "h": 8, "x": 0, "y": 5},
    "Rasio Validasi Gempa (STA / LTA)": {"w": 12, "h": 8, "x": 12, "y": 5},
    
    "Temperature (°C)": {"w": 12, "h": 8, "x": 0, "y": 13},
    "Barometric Pressure (hPa)": {"w": 12, "h": 8, "x": 12, "y": 13},
    
    "Current Tilt Angle": {"w": 8, "h": 8, "x": 0, "y": 21},
    "Network Latency (ESP32 to MQTT)": {"w": 16, "h": 8, "x": 8, "y": 21},
    
    "Physical Pose": {"w": 12, "h": 4, "x": 0, "y": 29},
    "Hardware Health (I2C)": {"w": 12, "h": 4, "x": 12, "y": 29},
    
    "🚨 Log Gempa Tervalidasi (Sistem Konsensus Multi-Node)": {"w": 24, "h": 8, "x": 0, "y": 33},
    "Actuator Valve Status": {"w": 12, "h": 6, "x": 0, "y": 41}
}

for p in dashboard.get('panels', []):
    title = p.get('title')
    if title in layout_map:
        p['gridPos'] = layout_map[title]

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'w') as f:
    json.dump(dashboard, f, indent=2)

