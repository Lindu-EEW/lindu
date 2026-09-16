import json

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'r') as f:
    dashboard = json.load(f)

for p in dashboard.get('panels', []):
    title = p.get('title', '')
    
    # 1. Lebarkan kembali top row tanpa Command Center
    if title == 'Active Nodes (Last 5 Min)':
        p['gridPos'] = {"w": 6, "h": 5, "x": 0, "y": 0}
    elif title == '📡 Live Fleet Status (Online / Offline)':
        p['gridPos'] = {"w": 18, "h": 5, "x": 6, "y": 0}
        
    # 2. Pindahkan Command Center ke paling bawah, full width (w=24)
    elif title == 'Interactive Command Center':
        p['gridPos'] = {"w": 24, "h": 6, "x": 0, "y": 50}
        
        # Sambil memperbaiki flexbox CSS di dalamnya agar menyebar secara horizontal
        html = p.get('options', {}).get('content', '')
        if 'flex-direction: row' not in html:
            # Rapikan layout command center agar tidak bertumpuk ke bawah
            html = html.replace('flex: 1;', 'flex: 1; min-width: 150px;')
            p['options']['content'] = html

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'w') as f:
    json.dump(dashboard, f, indent=2)

