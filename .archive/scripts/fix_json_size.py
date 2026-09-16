import re

with open('src/esp32_sensor_node/src/NetworkManager.cpp', 'r') as f:
    cpp = f.read()

cpp = cpp.replace('StaticJsonDocument<256> doc;', 'StaticJsonDocument<1024> doc;')

with open('src/esp32_sensor_node/src/NetworkManager.cpp', 'w') as f:
    f.write(cpp)

with open('src/esp32_sensor_node/src/OTAUpdater.h', 'r') as f:
    oh = f.read()

oh = oh.replace('#define CURRENT_VERSION "v1.1.30"', '#define CURRENT_VERSION "v1.1.31"')

with open('src/esp32_sensor_node/src/OTAUpdater.h', 'w') as f:
    f.write(oh)
