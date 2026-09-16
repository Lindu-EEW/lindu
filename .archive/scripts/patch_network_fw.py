import re

with open('src/esp32_sensor_node/src/NetworkManager.cpp', 'r') as f:
    content = f.read()

# Add #include "OTAUpdater.h" if not exists
if '#include "OTAUpdater.h"' not in content:
    content = '#include "OTAUpdater.h"\n' + content

# Modify publishStatus
old_payload = 'String statusPayload = "{\\"status\\":\\"" + status + "\\",\\"node_id\\":\\"" + String(_configMgr->config.node_id) + "\\",\\"lat\\":" + String(_configMgr->config.lat, 4) + ",\\"lon\\":" + String(_configMgr->config.lon, 4) + ",\\"pose\\":\\"" + pose + "\\",\\"tilt_angle\\":" + String(tilt_angle, 1) + ",\\"sensor_ok\\":" + String(sensor_ok ? "true" : "false") + "}";'
new_payload = 'String statusPayload = "{\\"status\\":\\"" + status + "\\",\\"node_id\\":\\"" + String(_configMgr->config.node_id) + "\\",\\"lat\\":" + String(_configMgr->config.lat, 4) + ",\\"lon\\":" + String(_configMgr->config.lon, 4) + ",\\"pose\\":\\"" + pose + "\\",\\"tilt_angle\\":" + String(tilt_angle, 1) + ",\\"sensor_ok\\":" + String(sensor_ok ? "true" : "false") + ",\\"fw_version\\":\\"" + String(CURRENT_VERSION) + "\\"}";'

content = content.replace(old_payload, new_payload)

with open('src/esp32_sensor_node/src/NetworkManager.cpp', 'w') as f:
    f.write(content)
