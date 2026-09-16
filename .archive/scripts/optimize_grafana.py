import json

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'r') as f:
    dashboard = json.load(f)

# =====================================================
# 1. Perbaiki tata letak: Hapus gap kosong akibat peta 
#    yang dihapus (y=5 sampai y=18 kosong 13 baris!)
# =====================================================
# Geser semua panel yang y >= 18 naik 13 baris
for panel in dashboard['panels']:
    if panel['gridPos']['y'] >= 18:
        panel['gridPos']['y'] -= 13

# =====================================================
# 2. Perkaya panel Log Gempa dengan kolom tambahan 
# =====================================================
for panel in dashboard['panels']:
    if panel.get('id') == 10:
        panel['targets'][0]['rawSql'] = """SELECT 
  time_alert AT TIME ZONE 'Asia/Tokyo' AS "Waktu Gempa (JST)", 
  magnitude AS "Magnitudo", 
  CASE 
    WHEN magnitude >= 7.0 THEN '🔴 Dahsyat'
    WHEN magnitude >= 6.0 THEN '🟠 Kuat' 
    WHEN magnitude >= 5.0 THEN '🟡 Sedang'
    ELSE '🟢 Ringan'
  END AS "Klasifikasi",
  radius_km AS "Radius (km)", 
  COALESCE(jsonb_array_length(triggering_nodes), 0) AS "Jumlah Node",
  description AS "Detail Analisis" 
FROM tb_system_alerts 
ORDER BY time_alert DESC LIMIT 20"""
        panel['title'] = '🚨 Log Gempa Tervalidasi (Konsensus Multi-Node)'

# =====================================================
# 3. Tambah panel BARU: PGA Gauge (Speedometer)
# =====================================================
pga_gauge = {
    "type": "gauge",
    "title": "🌊 PGA Terkini (Peak Ground Acceleration)",
    "id": 20,
    "gridPos": {"w": 12, "h": 8, "x": 0, "y": 5},
    "targets": [{
        "refId": "A",
        "rawSql": "SELECT pga AS \"PGA\" FROM tb_sensor_telemetry ORDER BY ts DESC LIMIT 1",
        "format": "table",
        "datasource": {"type": "grafana-postgresql-datasource", "uid": "lindu_pg"}
    }],
    "datasource": {"type": "grafana-postgresql-datasource", "uid": "lindu_pg"},
    "fieldConfig": {
        "defaults": {
            "unit": "g",
            "min": 0,
            "max": 2,
            "thresholds": {
                "mode": "absolute",
                "steps": [
                    {"color": "#73BF69", "value": None},
                    {"color": "#FADE2A", "value": 0.05},
                    {"color": "#FF9830", "value": 0.12},
                    {"color": "#F2495C", "value": 0.30},
                    {"color": "#8B0000", "value": 0.60}
                ]
            }
        }
    },
    "options": {
        "reduceOptions": {"calcs": ["lastNotNull"]},
        "showThresholdLabels": True,
        "showThresholdMarkers": True
    }
}

# =====================================================
# 4. Tambah panel BARU: Frekuensi Dominan Live
# =====================================================
freq_panel = {
    "type": "timeseries",
    "title": "🎵 Frekuensi Dominan (Hz) — Gempa < 15Hz, Noise > 20Hz",
    "id": 21,
    "gridPos": {"w": 12, "h": 8, "x": 12, "y": 5},
    "targets": [{
        "refId": "A",
        "rawSql": "SELECT ts AS time, freq_hz AS \"Frekuensi (Hz)\" FROM tb_sensor_telemetry WHERE $__timeFilter(ts) ORDER BY ts",
        "format": "time_series",
        "datasource": {"type": "grafana-postgresql-datasource", "uid": "lindu_pg"}
    }],
    "datasource": {"type": "grafana-postgresql-datasource", "uid": "lindu_pg"},
    "fieldConfig": {
        "defaults": {
            "unit": "Hz",
            "custom": {
                "drawStyle": "line",
                "lineWidth": 1,
                "fillOpacity": 20,
                "gradientMode": "scheme",
                "thresholdsStyle": {"mode": "area"}
            },
            "color": {"mode": "continuous-BlYlRd"},
            "thresholds": {
                "mode": "absolute",
                "steps": [
                    {"color": "#F2495C", "value": None},
                    {"color": "#73BF69", "value": 15},
                    {"color": "#FADE2A", "value": 20}
                ]
            }
        }
    }
}

dashboard['panels'].append(pga_gauge)
dashboard['panels'].append(freq_panel)

# =====================================================
# 5. Atur refresh rate optimal (5 detik)
# =====================================================
dashboard['refresh'] = '5s'

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'w') as f:
    json.dump(dashboard, f, indent=2)

