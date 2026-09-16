import json

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'r') as f:
    dashboard = json.load(f)

# 1. Hapus panel "Physical Pose" dan "Hardware Health (I2C)"
panels_to_remove = ["Physical Pose", "Hardware Health (I2C)"]
dashboard['panels'] = [p for p in dashboard.get('panels', []) if p.get('title') not in panels_to_remove]

# 2. Tambah tinggi Interactive Command Center
for p in dashboard.get('panels', []):
    if p.get('title') == 'Interactive Command Center':
        p['gridPos']['h'] = 9  # Naikkan dari 6 ke 9 agar lega
        
        # Sekalian kita pastikan flex-wrap CSS di dalamnya lebih nyaman
        html = p.get('options', {}).get('content', '')
        # Perbesar font atau padding jika perlu, tapi fokus utamanya h=9 sudah cukup
        pass

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'w') as f:
    json.dump(dashboard, f, indent=2)

