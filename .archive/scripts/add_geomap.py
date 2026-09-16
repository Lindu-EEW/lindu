import json

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'r') as f:
    dashboard = json.load(f)

# Buat panel geomap
geomap_panel = {
  "type": "geomap",
  "title": "🗺️ Live Seismic Map (Epicenter & Sensor Node)",
  "gridPos": {
    "h": 13,
    "w": 24,
    "x": 0,
    "y": 5
  },
  "datasource": {
    "type": "grafana-postgresql-datasource",
    "uid": "lindu_pg"
  },
  "targets": [
    {
      "format": "table",
      "rawSql": "SELECT n.node_id as name, n.lat as latitude, n.lon as longitude, CASE WHEN s.status = 'offline' THEN 0 ELSE 1 END as metric FROM tb_nodes n LEFT JOIN LATERAL (SELECT status FROM sensor_status WHERE node_id = n.node_id ORDER BY time DESC LIMIT 1) s ON true;",
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
      },
      "custom": {
        "hideFrom": {
          "tooltip": False,
          "viz": False,
          "legend": False
        }
      },
      "thresholds": {
        "mode": "absolute",
        "steps": [
          {
            "color": "red",
            "value": None
          },
          {
            "color": "green",
            "value": 1
          }
        ]
      }
    },
    "overrides": []
  },
  "options": {
    "view": {
      "id": "auto",
      "zoom": 10,
      "lat": 35.6,
      "lon": 139.6
    },
    "controls": {
      "mouseWheelZoom": True,
      "showAttribution": True,
      "showScale": True,
      "showZoom": True
    },
    "layers": [
      {
        "type": "markers",
        "name": "Sensor Nodes",
        "config": {
          "showLegend": True,
          "size": {
            "fixed": 15
          },
          "color": {
            "field": "metric"
          },
          "symbol": {
            "fixed": "img/icons/marker/circle.svg"
          },
          "text": {
            "field": "name",
            "config": {
              "offsetX": 0,
              "offsetY": 15
            }
          }
        },
        "location": {
          "mode": "auto"
        }
      }
    ],
    "basemap": {
      "type": "carto",
      "config": {
        "theme": "dark"
      },
      "name": "Layer 0"
    }
  }
}

# Geser panel lain ke bawah (semua yang y >= 5 ditambahkan 13)
for p in dashboard.get('panels', []):
    if p.get('gridPos', {}).get('y', 0) >= 5:
        p['gridPos']['y'] += 13

# Assign ID dan masukkan
max_id = max([p.get('id', 0) for p in dashboard.get('panels', [])])
geomap_panel['id'] = max_id + 1
dashboard['panels'].append(geomap_panel)

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'w') as f:
    json.dump(dashboard, f, indent=2)

