import re

with open('src/esp32_sensor_node/src/OtaUpdater.cpp', 'r') as f:
    content = f.read()

content = content.replace("86400000", "300000") # Ubah dari 24 Jam ke 5 Menit

with open('src/esp32_sensor_node/src/OtaUpdater.cpp', 'w') as f:
    f.write(content)
