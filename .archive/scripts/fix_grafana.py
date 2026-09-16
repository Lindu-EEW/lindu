import json

filepath = 'prototype/grafana-stack/grafana/dashboards/seismic.json'

with open(filepath, 'r') as f:
    data = json.load(f)

for panel in data.get("panels", []):
    if panel.get("title") == "💨 Konsentrasi Gas (MQ-2)":
        panel["targets"][0]["rawSql"] = 'SELECT ts AS "time", node_id AS "metric", gas_raw AS "Gas Level (Raw)" FROM tb_sensor_telemetry WHERE node_id IN ($node_id) AND ts > NOW() - INTERVAL \'15 minutes\' ORDER BY ts ASC'
        break

with open(filepath, 'w') as f:
    json.dump(data, f, indent=2)

