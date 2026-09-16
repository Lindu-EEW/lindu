import re

with open('src/esp32_sensor_node/src/main.cpp', 'r') as f:
    content = f.read()

# Add include
if '#include "OTAUpdater.h"' not in content:
    content = content.replace('#include "SensorManager.h"', '#include "SensorManager.h"\n#include "OTAUpdater.h"')

# Add begin in setup()
if 'otaUpdater.begin();' not in content:
    content = content.replace('sensorMgr.begin(eventQueue);', 'sensorMgr.begin(eventQueue);\n    otaUpdater.begin();')

# Add loop in networkTaskCode
if 'otaUpdater.loop();' not in content:
    # insert inside while(1) of networkTaskCode
    content = content.replace('if (WiFi.status() == WL_CONNECTED) {', 'if (WiFi.status() == WL_CONNECTED) {\n            otaUpdater.loop();')

with open('src/esp32_sensor_node/src/main.cpp', 'w') as f:
    f.write(content)
print("Patched main.cpp")
