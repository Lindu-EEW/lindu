import re

with open('src/esp32_sensor_node/src/OtaUpdater.cpp', 'r') as f:
    content = f.read()

# Force inject after #include "OTAUpdater.h"
old_header = '#include "OTAUpdater.h"'
new_header = '#include "OTAUpdater.h"\n#include <Adafruit_NeoPixel.h>\nextern Adafruit_NeoPixel pixels;'

if "extern Adafruit_NeoPixel pixels;" not in content:
    content = content.replace(old_header, new_header)

with open('src/esp32_sensor_node/src/OtaUpdater.cpp', 'w') as f:
    f.write(content)
