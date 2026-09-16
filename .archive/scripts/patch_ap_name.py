import re

with open('src/esp32_sensor_node/src/ConfigManager.cpp', 'r') as f:
    content = f.read()

# Replace hardcoded "Lindu_Setup" with config.node_id
old_code = 'if (!wm.autoConnect("Lindu_Setup")) {'
new_code = 'if (!wm.autoConnect(config.node_id)) {'

content = content.replace(old_code, new_code)

with open('src/esp32_sensor_node/src/ConfigManager.cpp', 'w') as f:
    f.write(content)

print("AP Name Patched")
