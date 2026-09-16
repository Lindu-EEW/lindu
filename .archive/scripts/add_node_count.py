import json

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'r') as f:
    dashboard = json.load(f)

# Shift all existing panels down by 4 units
for panel in dashboard.get('panels', []):
    panel['gridPos']['y'] += 4

# Create the new Stat panel
stat_panel = {
  "type": "stat",
  "title": "Active Nodes (Last 5 Min)",
  "gridPos": {
    "h": 4,
    "w": 24,
    "x": 0,
    "y": 0
  },
  "targets": [
    {
      "refId": "A",
      "rawSql": "SELECT count(DISTINCT node_id) as count FROM sensor_telemetry WHERE time > NOW() - INTERVAL '5 minutes'",
      "format": "table",
      "datasource": {
        "type": "grafana-postgresql-datasource",
        "uid": "lindu_pg"
      }
    }
  ],
  "datasource": {
    "type": "grafana-postgresql-datasource",
    "uid": "lindu_pg"
  },
  "options": {
    "colorMode": "value",
    "graphMode": "none",
    "justifyMode": "center",
    "text": {}
  },
  "fieldConfig": {
    "defaults": {
      "mappings": [],
      "thresholds": {
        "mode": "absolute",
        "steps": [
          { "color": "red", "value": None },
          { "color": "green", "value": 1 }
        ]
      },
      "color": {
        "mode": "thresholds"
      }
    },
    "overrides": []
  }
}

dashboard['panels'].insert(0, stat_panel)

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'w') as f:
    json.dump(dashboard, f, indent=2)

