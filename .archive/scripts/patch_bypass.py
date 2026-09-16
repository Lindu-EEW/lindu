import re
with open('src/esp32_sensor_node/src/NetworkManager.cpp', 'r') as f:
    content = f.read()

old_logic = """            bool is_unprovisioned = (instance->_configMgr->config.lat == 0.0 && instance->_configMgr->config.lon == 0.0);
            
            if (dist < 50.0 || is_unprovisioned) {"""

new_logic = """            bool is_bypass = doc["bypass"] | false;
            
            if (dist < 50.0 || is_bypass) {"""

content = content.replace(old_logic, new_logic)

with open('src/esp32_sensor_node/src/NetworkManager.cpp', 'w') as f:
    f.write(content)
