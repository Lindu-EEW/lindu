import re

with open('prototype/grafana-stack/ingester/ingester.py', 'r') as f:
    content = f.read()

# 1. Extract fw_version
old_sensor_ok = "sensor_ok = payload.get(\"sensor_ok\", False)"
new_sensor_ok = "sensor_ok = payload.get(\"sensor_ok\", False)\n            fw_version = payload.get(\"fw_version\", \"UNKNOWN\")"
content = content.replace(old_sensor_ok, new_sensor_ok)

# 2. Append to buffer
old_append = "status_buffer.append((now, node_id, status, pose, tilt, latency, sensor_ok))"
new_append = "status_buffer.append((now, node_id, status, pose, tilt, latency, sensor_ok, fw_version))"
content = content.replace(old_append, new_append)

# 3. Update SQL
old_sql = "INSERT INTO sensor_status (time, node_id, status, pose, tilt_angle, latency_ms, sensor_ok) VALUES (%s, %s, %s, %s, %s, %s, %s)"
new_sql = "INSERT INTO sensor_status (time, node_id, status, pose, tilt_angle, latency_ms, sensor_ok, fw_version) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
content = content.replace(old_sql, new_sql)

with open('prototype/grafana-stack/ingester/ingester.py', 'w') as f:
    f.write(content)
