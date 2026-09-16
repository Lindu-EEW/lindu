import re

# 1. Update NetworkManager.h
with open('src/esp32_sensor_node/src/NetworkManager.h', 'r') as f:
    nh = f.read()
if "void forcePublishStatus();" not in nh:
    nh = nh.replace('void publishStatus(', 'void forcePublishStatus();\n    void publishStatus(')
with open('src/esp32_sensor_node/src/NetworkManager.h', 'w') as f:
    f.write(nh)

# 2. Update NetworkManager.cpp
with open('src/esp32_sensor_node/src/NetworkManager.cpp', 'r') as f:
    n_cpp = f.read()

force_pub_func = '''void NetworkManager::forcePublishStatus() {
    publishStatus("online", true, 0.0, "FLAT");
}

void NetworkManager::publishStatus('''

if "forcePublishStatus()" not in n_cpp:
    n_cpp = n_cpp.replace('void NetworkManager::publishStatus(', force_pub_func)

with open('src/esp32_sensor_node/src/NetworkManager.cpp', 'w') as f:
    f.write(n_cpp)

# 3. Update OtaUpdater.cpp
with open('src/esp32_sensor_node/src/OtaUpdater.cpp', 'r') as f:
    o_cpp = f.read()

# Add extern
if "extern NetworkManager networkMgr;" not in o_cpp:
    o_cpp = o_cpp.replace('#include "OTAUpdater.h"', '#include "OTAUpdater.h"\n#include "NetworkManager.h"\nextern NetworkManager networkMgr;')

# Replace ota_status assignments with force publishing
o_cpp = o_cpp.replace('ota_status = "CHECKING_GITHUB";', 'ota_status = "CHECKING_GITHUB"; networkMgr.forcePublishStatus();')
o_cpp = o_cpp.replace('ota_status = "DOWNLOADING_v1.1.0";', 'ota_status = "DOWNLOADING_FIRMWARE"; networkMgr.forcePublishStatus();')
o_cpp = o_cpp.replace('ota_status = "UP_TO_DATE";', 'ota_status = "UP_TO_DATE"; networkMgr.forcePublishStatus();')
o_cpp = o_cpp.replace('ota_status = "UPDATE_SUCCESS_RESTARTING";', 'ota_status = "UPDATE_SUCCESS_RESTARTING"; networkMgr.forcePublishStatus();')

with open('src/esp32_sensor_node/src/OtaUpdater.cpp', 'w') as f:
    f.write(o_cpp)

