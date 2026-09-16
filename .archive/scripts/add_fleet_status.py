import json

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'r') as f:
    dashboard = json.load(f)

# Buat panel baru untuk Status Node
fleet_panel = {
  "type": "table",
  "title": "📡 Live Fleet Status (Online / Offline)",
  "gridPos": {
    "h": 5,
    "w": 8,
    "x": 8,
    "y": 0
  },
  "datasource": {
    "type": "grafana-postgresql-datasource",
    "uid": "lindu_pg"
  },
  "targets": [
    {
      "format": "table",
      "rawSql": "SELECT DISTINCT ON (node_id) node_id as \"Node ID\", CASE WHEN status = 'offline' THEN 'OFFLINE' ELSE 'ONLINE' END as \"Status\", fw_version as \"Firmware\", time as \"Last Seen\" FROM sensor_status WHERE node_id IN ($node) AND time >= NOW() - INTERVAL '1 hour' ORDER BY node_id, time DESC;",
      "refId": "A",
      "datasource": {
        "type": "grafana-postgresql-datasource",
        "uid": "lindu_pg"
      }
    }
  ],
  "fieldConfig": {
    "defaults": {
      "color": {
        "mode": "thresholds"
      }
    },
    "overrides": [
      {
        "matcher": {
          "id": "byName",
          "options": "Status"
        },
        "properties": [
          {
            "id": "color",
            "value": {
              "mode": "fixed",
              "fixedColor": "green"
            }
          },
          {
            "id": "mappings",
            "value": [
              {
                "type": "value",
                "options": {
                  "OFFLINE": {
                    "color": "red",
                    "index": 0,
                    "text": "🔴 OFFLINE"
                  },
                  "ONLINE": {
                    "color": "green",
                    "index": 1,
                    "text": "🟢 ONLINE"
                  }
                }
              }
            ]
          }
        ]
      }
    ]
  },
  "options": {
    "showHeader": True,
    "sortBy": [
      {
        "desc": False,
        "displayName": "Status"
      }
    ]
  }
}

# Geser panel lain agar ada ruang di grid
for p in dashboard.get('panels', []):
    if p.get('type') == 'stat' and p.get('title') == 'Active Nodes (Last 5 Min)':
        p['gridPos'] = {"h": 5, "w": 4, "x": 0, "y": 0} # Perkecil stat panel

    # Geser panel baris atas ke kanan atau turun
    if p.get('gridPos', {}).get('y', 0) == 0 and p.get('title') not in ['Active Nodes (Last 5 Min)', 'Interactive Command Center']:
        p['gridPos']['y'] += 5

# Set Interactive Command center ke kiri
for p in dashboard.get('panels', []):
    if p.get('title') == 'Interactive Command Center':
        p['gridPos'] = {"h": 5, "w": 4, "x": 4, "y": 0}

dashboard['panels'].insert(0, fleet_panel)

# Cari dan set ID untuk mencegah konflik
max_id = 0
for p in dashboard['panels']:
    if p.get('id', 0) > max_id:
        max_id = p.get('id', 0)
        
fleet_panel['id'] = max_id + 1

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'w') as f:
    json.dump(dashboard, f, indent=2)

