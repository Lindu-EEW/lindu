import json

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'r') as f:
    dash = json.load(f)

for p in dash.get('panels', []):
    if p.get('id') == 13: # Command Center panel
        content = p['options']['content']
        
        # 1. Hapus Input Text targetNode
        target_input = '''  <div style="display: flex; gap: 10px; flex-wrap: wrap;">
    <input type="text" id="targetNode" placeholder="Target Node (e.g., node_3c096f0c atau all)" value="all" style="padding: 8px; background: #24283b; color: #fff; border: 1px solid #414868; border-radius: 4px; flex: 1; min-width: 150px; min-width: 200px;">
  </div>'''
        
        replacement_input = '''  <div style="display: flex; gap: 10px; flex-wrap: wrap; background: #24283b; padding: 10px; border-radius: 4px; border: 1px solid #414868;">
    <p style="color: #9ece6a; margin: 0; font-size: 13px;"><b>Target Aktif:</b> <span id="displayTarget" style="color:white; font-family: monospace;">${node_id:raw}</span> <i style="color:#9aa5ce; font-size:11px;">(Mengikuti Dropdown di Atas)</i></p>
  </div>'''
        
        content = content.replace(target_input, replacement_input)
        
        # 2. Ubah Javascript untuk mengambil dari target
        target_js = '''    const target = document.getElementById('targetNode').value || 'all';'''
        replacement_js = '''    let target = '${node_id:raw}';
    if (target.includes('__all') || target.toLowerCase() === 'all' || target === '') {
        target = 'all';
    }
'''
        content = content.replace(target_js, replacement_js)
        
        p['options']['content'] = content
        break

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'w') as f:
    json.dump(dash, f, indent=2)

