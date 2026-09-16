with open('src/esp32_sensor_node/src/NetworkManager.cpp', 'r') as f:
    n_content = f.read()

target = ',\\"fw_version\\":\\"" + String(CURRENT_VERSION) + "\\"}";'
replacement = ',\\"fw_version\\":\\"" + String(CURRENT_VERSION) + "\\",\\"ota_status\\":\\"" + otaUpdater.ota_status + "\\"}";'
n_content = n_content.replace(target, replacement)

with open('src/esp32_sensor_node/src/NetworkManager.cpp', 'w') as f:
    f.write(n_content)

with open('src/esp32_sensor_node/src/OtaUpdater.cpp', 'r') as f:
    o_content = f.read()

o_content = o_content.replace('pixels.Color(0, 255, 255)', 'pixels.Color(255, 255, 0)')
o_content = o_content.replace('Cyan = Updating', 'Yellow = Updating')

with open('src/esp32_sensor_node/src/OtaUpdater.cpp', 'w') as f:
    f.write(o_content)
