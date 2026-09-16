import json

# ==========================================
# 1. TAMBAH TOMBOL DI GRAFANA COMMAND CENTER
# ==========================================
with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'r') as f:
    dash = json.load(f)

for p in dash.get('panels', []):
    if p.get('id') == 13: # Command Center panel
        content = p['options']['content']
        
        # Inject Debug Buttons
        target_btns = '''  <div style="display: flex; gap: 10px; margin-top: 15px; flex-wrap: wrap;">
    <button onclick="sendCmd('disable_valve')" style="background: #f7768e; color: #1a1b26; font-weight: bold; border: none; padding: 10px 15px; border-radius: 4px; cursor: pointer; flex: 1; min-width: 150px;"><i class="fa fa-lock"></i> LOCK VALVE</button>'''
        
        replacement_btns = '''  <div style="display: flex; gap: 10px; margin-top: 15px; flex-wrap: wrap;">
    <button onclick="sendCmd('enable_debug')" style="background: #00E5FF; color: #1a1b26; font-weight: bold; border: none; padding: 10px 15px; border-radius: 4px; cursor: pointer; flex: 1; min-width: 150px;"><i class="fa fa-bug"></i> ENABLE DEBUG LOG</button>
    <button onclick="sendCmd('disable_debug')" style="background: #414868; color: #ffffff; font-weight: bold; border: none; padding: 10px 15px; border-radius: 4px; cursor: pointer; flex: 1; min-width: 150px;"><i class="fa fa-ban"></i> DISABLE DEBUG</button>
  </div>
  <div style="display: flex; gap: 10px; margin-top: 15px; flex-wrap: wrap;">
    <button onclick="sendCmd('disable_valve')" style="background: #f7768e; color: #1a1b26; font-weight: bold; border: none; padding: 10px 15px; border-radius: 4px; cursor: pointer; flex: 1; min-width: 150px;"><i class="fa fa-lock"></i> LOCK VALVE</button>'''
        
        new_content = content.replace(target_btns, replacement_btns)
        p['options']['content'] = new_content
        break

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'w') as f:
    json.dump(dash, f, indent=2)

