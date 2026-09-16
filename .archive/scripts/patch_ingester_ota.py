import re

with open('prototype/grafana-stack/ingester/ingester.py', 'r') as f:
    content = f.read()

# Replace INSERT statement
old_insert = '"INSERT INTO sensor_status (time, node_id, status, pose, tilt_angle, latency_ms, sensor_ok, fw_version) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",'
new_insert = '"INSERT INTO sensor_status (time, node_id, status, pose, tilt_angle, latency_ms, sensor_ok, fw_version, ota_status) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",'
content = content.replace(old_insert, new_insert)

# Replace buffer append logic
old_parse = """            fw_version = payload.get("fw_version", "UNKNOWN")
            with buffer_lock:
                status_buffer.append((now, node_id, status, pose, tilt, latency, sensor_ok, fw_version))"""

new_parse = """            fw_version = payload.get("fw_version", "UNKNOWN")
            ota_status = payload.get("ota_status", "IDLE")
            with buffer_lock:
                status_buffer.append((now, node_id, status, pose, tilt, latency, sensor_ok, fw_version, ota_status))"""

content = content.replace(old_parse, new_parse)

with open('prototype/grafana-stack/ingester/ingester.py', 'w') as f:
    f.write(content)
