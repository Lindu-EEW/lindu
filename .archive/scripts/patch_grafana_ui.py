import json

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'r') as f:
    dashboard = json.load(f)

for p in dashboard.get('panels', []):
    if p.get('title') == 'Interactive Command Center':
        # Modify the HTML script to handle set_location
        html = p['options']['content']
        
        target_inputs = '''<input type="text" id="targetNode" placeholder="Target Node (e.g., node_3c096f0c atau all)" value="all" style="padding: 8px; background: #24283b; color: #fff; border: 1px solid #414868; border-radius: 4px; flex: 1; min-width: 200px;">
  </div>'''
        
        replace_inputs = '''<input type="text" id="targetNode" placeholder="Target Node (e.g., node_3c096f0c atau all)" value="all" style="padding: 8px; background: #24283b; color: #fff; border: 1px solid #414868; border-radius: 4px; flex: 1; min-width: 200px;">
  </div>
  
  <div style="display: flex; gap: 10px; margin-top: 10px; flex-wrap: wrap; background: #1f2335; padding: 10px; border-radius: 4px;">
    <input type="number" id="newLat" placeholder="New Latitude (e.g. -6.123)" step="0.0001" style="padding: 8px; background: #24283b; color: #fff; border: 1px solid #414868; border-radius: 4px; flex: 1; min-width: 100px;">
    <input type="number" id="newLon" placeholder="New Longitude (e.g. 106.123)" step="0.0001" style="padding: 8px; background: #24283b; color: #fff; border: 1px solid #414868; border-radius: 4px; flex: 1; min-width: 100px;">
    <button onclick="sendCmd('set_location')" style="background: #bb9af7; color: #1a1b26; font-weight: bold; border: none; padding: 10px 15px; border-radius: 4px; cursor: pointer;"><i class="fa fa-map-marker"></i> SET KOORDINAT BARU</button>
  </div>'''
  
        target_fetch = '''body: JSON.stringify({ cmd: command, target_node: target })'''
        replace_fetch = '''body: JSON.stringify({ cmd: command, target_node: target, lat: document.getElementById('newLat').value, lon: document.getElementById('newLon').value })'''
        
        if "newLat" not in html:
            html = html.replace(target_inputs, replace_inputs)
            html = html.replace(target_fetch, replace_fetch)
            p['options']['content'] = html

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'w') as f:
    json.dump(dashboard, f, indent=2)

