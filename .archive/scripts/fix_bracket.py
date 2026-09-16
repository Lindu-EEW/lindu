import re

with open('src/esp32_sensor_node/src/NetworkManager.cpp', 'r') as f:
    content = f.read()

content = content.replace("}\n}\n\nbool NetworkManager::isConnected()", "}\n\nbool NetworkManager::isConnected()")

with open('src/esp32_sensor_node/src/NetworkManager.cpp', 'w') as f:
    f.write(content)
