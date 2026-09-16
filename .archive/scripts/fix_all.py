import re

with open('src/esp32_sensor_node/src/NetworkManager.cpp', 'r') as f:
    n_content = f.read()

# Fix NetworkManager JSON payload to include ota_status properly
if "ota_status" not in n_content:
    old_str = ',"fw_version":"\' + String(CURRENT_VERSION) + \'"}\';'
    new_str = ',"fw_version":"\' + String(CURRENT_VERSION) + \'","ota_status":"\' + otaUpdater.ota_status + \'"}\';'
    # Use regex to be safe
    n_content = re.sub(r',"fw_version":"\\\' \+ String\(CURRENT_VERSION\) \+ \\'"}\\';', new_str, n_content)
    # The literal in cpp is: ,"fw_version\":\"" + String(CURRENT_VERSION) + "\"}"
    n_content = n_content.replace(',\\"fw_version\\":\\"" + String(CURRENT_VERSION) + "\\"}";', ',\\"fw_version\\":\\"" + String(CURRENT_VERSION) + "\\",\\"ota_status\\":\\"" + otaUpdater.ota_status + "\\"}";')

with open('src/esp32_sensor_node/src/NetworkManager.cpp', 'w') as f:
    f.write(n_content)

# Change OTA color to Yellow (255, 255, 0)
with open('src/esp32_sensor_node/src/OtaUpdater.cpp', 'r') as f:
    o_content = f.read()

o_content = o_content.replace('pixels.Color(0, 255, 255)', 'pixels.Color(255, 255, 0)')
o_content = o_content.replace('// Cyan = Updating', '// Yellow = Updating')

with open('src/esp32_sensor_node/src/OtaUpdater.cpp', 'w') as f:
    f.write(o_content)
