import json
import re

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'r') as f:
    dashboard = json.load(f)

for p in dashboard.get('panels', []):
    if p.get('title') == 'Interactive Command Center':
        # Add Reset button to the HTML string
        target_html = '''<button onclick="sendCommand('force_update', 'all')" style="width: 100%; padding: 10px; margin-bottom: 10px; background-color: #3498db; color: white; border: none; cursor: pointer; border-radius: 4px; font-weight: bold;">[📡] FORCE OTA UPDATE</button>'''
        replace_html = target_html + '''\n    <button onclick="if(confirm('Yakin ingin mereset WiFi & Koordinat? Node akan kembali jadi Access Point.')) sendCommand('factory_reset', 'all')" style="width: 100%; padding: 10px; margin-bottom: 10px; background-color: #e74c3c; color: white; border: none; cursor: pointer; border-radius: 4px; font-weight: bold;">[🔥] FACTORY RESET NODE</button>'''
        
        if "factory_reset" not in p['options']['content']:
            p['options']['content'] = p['options']['content'].replace(target_html, replace_html)

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'w') as f:
    json.dump(dashboard, f, indent=2)

