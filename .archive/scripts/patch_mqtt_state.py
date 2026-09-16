import re

# 1. Update NetworkManager.h
with open('src/esp32_sensor_node/src/NetworkManager.h', 'r') as f:
    h_content = f.read()

if 'bool isConnected();' not in h_content:
    h_content = h_content.replace('void loop();', 'void loop();\n    bool isConnected();\n    void publishStatus(String status, bool sensor_ok, float tilt_angle, String pose);')

with open('src/esp32_sensor_node/src/NetworkManager.h', 'w') as f:
    f.write(h_content)

# 2. Update NetworkManager.cpp
with open('src/esp32_sensor_node/src/NetworkManager.cpp', 'r') as f:
    cpp_content = f.read()

if 'bool NetworkManager::isConnected()' not in cpp_content:
    cpp_content += "\nbool NetworkManager::isConnected() {\n    return mqtt.connected();\n}\n"

with open('src/esp32_sensor_node/src/NetworkManager.cpp', 'w') as f:
    f.write(cpp_content)

# 3. Update main.cpp LED logic
with open('src/esp32_sensor_node/src/main.cpp', 'r') as f:
    main_content = f.read()

old_wifi_check = "if (WiFi.status() == WL_CONNECTED) {"
new_wifi_check = "if (WiFi.status() == WL_CONNECTED && networkMgr.isConnected()) {"

main_content = main_content.replace(old_wifi_check, new_wifi_check)

with open('src/esp32_sensor_node/src/main.cpp', 'w') as f:
    f.write(main_content)

print("MQTT State Patched")
