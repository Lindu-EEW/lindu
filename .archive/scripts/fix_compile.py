import re

with open('src/esp32_sensor_node/src/main.cpp', 'r') as f:
    cpp = f.read()

if '<sys/time.h>' not in cpp:
    cpp = cpp.replace('#include <Arduino.h>', '#include <Arduino.h>\n#include <sys/time.h>')

with open('src/esp32_sensor_node/src/main.cpp', 'w') as f:
    f.write(cpp)

with open('src/esp32_sensor_node/src/OTAUpdater.h', 'r') as f:
    oh = f.read()
oh = oh.replace('#define CURRENT_VERSION "v1.1.33"', '#define CURRENT_VERSION "v1.1.34"')
with open('src/esp32_sensor_node/src/OTAUpdater.h', 'w') as f:
    f.write(oh)

