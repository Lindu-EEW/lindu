import json
import os

filepath = 'prototype/grafana-stack/grafana/dashboards/seismic.json'

with open(filepath, 'r') as f:
    data = json.load(f)

# Find highest Y coordinate to put the panel at the bottom
max_y = max((panel.get("gridPos", {}).get("y", 0) for panel in data.get("panels", [])), default=0)

gas_panel = {
  "type": "timeseries",
  "title": "💨 Konsentrasi Gas (MQ-2)",
  "gridPos": {
    "h": 8,
    "w": 12,
    "x": 0,
    "y": max_y + 8
  },
  "datasource": {
    "type": "grafana-postgresql-datasource",
    "uid": "lindu_pg"
  },
  "targets": [
    {
      "format": "time_series",
      "group": [],
      "metricColumn": "none",
      "rawQuery": True,
      "rawSql": "SELECT\n  $__timeGroupAlias(ts, '1s'),\n  avg(gas_raw) AS \"Gas Level (Raw)\"\nFROM tb_sensor_telemetry\nWHERE\n  $__timeFilter(ts) AND\n  node_id IN (${node_id:raw})\nGROUP BY 1\nORDER BY 1",
      "refId": "A"
    }
  ],
  "options": {
    "tooltip": {
      "mode": "single",
      "sort": "none"
    },
    "legend": {
      "displayMode": "list",
      "placement": "bottom",
      "showLegend": True
    }
  },
  "fieldConfig": {
    "defaults": {
      "custom": {
        "drawStyle": "line",
        "lineInterpolation": "linear",
        "lineWidth": 2,
        "fillOpacity": 20,
        "spanNulls": False
      },
      "color": {
        "mode": "fixed",
        "fixedColor": "orange"
      },
      "thresholds": {
        "mode": "absolute",
        "steps": [
          {
            "color": "green",
            "value": None
          },
          {
            "color": "red",
            "value": 1800
          }
        ]
      }
    }
  }
}

data["panels"].append(gas_panel)

with open(filepath, 'w') as f:
    json.dump(data, f, indent=2)

print("Berhasil menambahkan panel Gas!")
