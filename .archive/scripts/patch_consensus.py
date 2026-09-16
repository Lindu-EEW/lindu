with open('src/server/consensus.py', 'r') as f:
    content = f.read()

# Replace the first INSERT
content = content.replace(
    'INSERT INTO tb_sensor_telemetry (ts, node_id, pga, sta_lta, freq_hz, ax, ay, az, lat, lon, uptime_ms)\n                VALUES (to_timestamp(%s), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);',
    'INSERT INTO tb_sensor_telemetry (ts, node_id, pga, sta_lta, freq_hz, ax, ay, az, lat, lon, uptime_ms, gas_raw, gas_alert, door_status, valve_status)\n                VALUES (to_timestamp(%s), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);'
)

content = content.replace(
    'payload.get("uptime_ms", 0)\n            ))',
    'payload.get("uptime_ms", 0),\n                payload.get("gas_raw", 0),\n                payload.get("gas_alert", False),\n                payload.get("door_status", "UNKNOWN"),\n                payload.get("valve_status", "UNKNOWN")\n            ))'
)

# Replace the second INSERT
content = content.replace(
    'INSERT INTO tb_sensor_telemetry (ts, node_id, pga, sta_lta, freq_hz, ax, ay, az, lat, lon, uptime_ms)\n                VALUES (NOW(), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);',
    'INSERT INTO tb_sensor_telemetry (ts, node_id, pga, sta_lta, freq_hz, ax, ay, az, lat, lon, uptime_ms, gas_raw, gas_alert, door_status, valve_status)\n                VALUES (NOW(), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);'
)

with open('src/server/consensus.py', 'w') as f:
    f.write(content)

