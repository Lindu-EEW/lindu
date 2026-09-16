import re

with open('src/esp32_sensor_node/src/main.cpp', 'r') as f:
    cpp = f.read()

# Fix the invalid struct fields I accidentally injected
cpp = cpp.replace('WiFi.begin(configMgr.config.wifi_ssid, configMgr.config.wifi_pass);', 'WiFi.begin(); // Menggunakan memori NVS bawaan ESP32')

with open('src/esp32_sensor_node/src/main.cpp', 'w') as f:
    f.write(cpp)
