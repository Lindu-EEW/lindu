import re

# 1. Update OTAUpdater.h
with open('src/esp32_sensor_node/src/OTAUpdater.h', 'r') as f:
    h_content = f.read()

if "String ota_status" not in h_content:
    h_content = h_content.replace("void confirmWorking();", "void confirmWorking();\n    String ota_status = \"IDLE\";")
    with open('src/esp32_sensor_node/src/OTAUpdater.h', 'w') as f:
        f.write(h_content)

# 2. Update NetworkManager.cpp
with open('src/esp32_sensor_node/src/NetworkManager.cpp', 'r') as f:
    n_content = f.read()

old_payload = ',"fw_version":"\' + String(CURRENT_VERSION) + \'"}\';'
new_payload = ',"fw_version":"\' + String(CURRENT_VERSION) + \'","ota_status":"\' + otaUpdater.ota_status + \'"}\';'
if "ota_status" not in n_content:
    n_content = n_content.replace(old_payload, new_payload)
    with open('src/esp32_sensor_node/src/NetworkManager.cpp', 'w') as f:
        f.write(n_content)

# 3. Update OtaUpdater.cpp
with open('src/esp32_sensor_node/src/OTAUpdater.cpp', 'r') as f:
    cpp_content = f.read()

# I will just write a new OTAUpdater.cpp entirely for safety, it's easier.
