import re

with open('src/esp32_sensor_node/src/NetworkManager.cpp', 'r') as f:
    cpp = f.read()

target = 'mqtt.publish(topic, payload, 0, false); // QoS 0, no retain for logs'
replacement = 'mqtt.publish(topic, payload); // Menggunakan overload string (otomatis QoS 0, retain false)'

cpp = cpp.replace(target, replacement)

with open('src/esp32_sensor_node/src/NetworkManager.cpp', 'w') as f:
    f.write(cpp)
