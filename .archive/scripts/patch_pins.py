import re

with open('src/esp32_sensor_node/src/SensorManager.cpp', 'r') as f:
    content = f.read()

content = content.replace('Wire1.begin(10, 11);', 'Wire1.begin(15, 16);')

with open('src/esp32_sensor_node/src/SensorManager.cpp', 'w') as f:
    f.write(content)
