import re

with open('src/esp32_sensor_node/src/ConfigManager.cpp', 'r') as f:
    content = f.read()

content = content.replace("WiFiManager wm;", "WiFi.mode(WIFI_STA);\n    WiFiManager wm;")

with open('src/esp32_sensor_node/src/ConfigManager.cpp', 'w') as f:
    f.write(content)

print("WiFi STA Patched")
