import json

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'r') as f:
    dashboard = json.load(f)

for panel in dashboard['panels']:
    if 'Command Center' in panel.get('title', ''):
        content = panel.get('options', {}).get('content', '')
        
        # Tambahkan tombol Restart Server
        new_btn = '''  <div style="flex: 1; min-width: 150px;">
    <button id="btn-restart" style="width: 100%; padding: 12px; background-color: #8E44AD; color: white; border: none; border-radius: 6px; font-weight: bold; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 8px;">
      <span style="font-size: 16px;">🔄</span> RESTART SERVER
    </button>
  </div>'''
        
        # Sisipkan setelah btn-reset
        content = content.replace('<!-- END TOMBOL -->', new_btn + '\n  <!-- END TOMBOL -->')
        
        # Tambahkan event listener JS
        new_js = '''
document.getElementById('btn-restart').onclick = function() {
    if(confirm('⚠️ PERINGATAN: Ini akan merestart sistem konsensus (Backend Python) di Raspberry Pi! Yakin?')) {
        fetch('http://localhost:5000/api/cmd', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({cmd: 'restart_server', target_node: 'all'})
        }).then(r => alert('Server sedang di-restart!'));
    }
};'''
        content = content.replace('// --- EVENT LISTENERS ---', '// --- EVENT LISTENERS ---' + new_js)
        
        panel['options']['content'] = content

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'w') as f:
    json.dump(dashboard, f, indent=2)

