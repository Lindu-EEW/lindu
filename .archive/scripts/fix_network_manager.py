import re

with open('src/esp32_sensor_node/src/NetworkManager.cpp', 'r') as f:
    content = f.read()

content = content.replace("is_global_alarm = true;", "")

with open('src/esp32_sensor_node/src/NetworkManager.cpp', 'w') as f:
    f.write(content)

with open('src/esp32_sensor_node/src/NetworkManager.h', 'r') as f:
    content = f.read()

content = content.replace("extern bool is_global_alarm;", "")

with open('src/esp32_sensor_node/src/NetworkManager.h', 'w') as f:
    f.write(content)
