import json
import re

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'r') as f:
    dashboard = json.load(f)

for p in dashboard.get('panels', []):
    if p.get('title') == 'Interactive Command Center':
        html = p.get('options', {}).get('content', '')
        
        # Tambahkan form MQTT Broker jika belum ada
        if "Set New Broker IP" not in html:
            # Cari letak tombol SET LOCATION untuk menyisipkan
            insert_pos = html.find('</div>', html.find('set_location')) + 6
            
            new_form = """
            <div style="padding:10px; border:1px solid #73BF69; border-radius:5px; margin-bottom:10px; text-align:center;">
                <h4>🌐 Migrasi Server (Staging/Production)</h4>
                <input type="text" id="new_broker" placeholder="mqtt.lindu-eew.com" style="padding:5px; color:black;">
                <button onclick="sendCmd('set_broker')" style="padding:5px 15px; background:#73BF69; color:white; border:none; border-radius:3px;">MIGRATE TO NEW SERVER</button>
            </div>
            """
            
            html = html[:insert_pos] + new_form + html[insert_pos:]
            
            # Update JS sendCmd
            js_target = """        if (cmd === 'set_location') {
            body.lat = parseFloat(document.getElementById('new_lat').value);
            body.lon = parseFloat(document.getElementById('new_lon').value);
        }"""
            
            js_replace = """        if (cmd === 'set_location') {
            body.lat = parseFloat(document.getElementById('new_lat').value);
            body.lon = parseFloat(document.getElementById('new_lon').value);
        } else if (cmd === 'set_broker') {
            body.server = document.getElementById('new_broker').value;
        }"""
            
            html = html.replace(js_target, js_replace)
            p['options']['content'] = html

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'w') as f:
    json.dump(dashboard, f, indent=2)

