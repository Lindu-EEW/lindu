import re

with open('src/esp32_sensor_node/src/main.cpp', 'r') as f:
    main_code = f.read()
if '<esp_attr.h>' not in main_code:
    main_code = main_code.replace('#include <Arduino.h>', '#include <Arduino.h>\n#include <esp_attr.h>')
with open('src/esp32_sensor_node/src/main.cpp', 'w') as f:
    f.write(main_code)

with open('src/esp32_sensor_node/src/NetworkManager.cpp', 'r') as f:
    nm_code = f.read()
nm_code = nm_code.replace('doc["server"].as<const char*>()', '(const char*)doc["server"]')
with open('src/esp32_sensor_node/src/NetworkManager.cpp', 'w') as f:
    f.write(nm_code)

with open('src/esp32_sensor_node/.github/workflows/ota_release.yml', 'r') as f:
    gh = f.read()

gh = gh.replace('pip install platformio', 'pip install -U platformio\n          pio update')
with open('src/esp32_sensor_node/.github/workflows/ota_release.yml', 'w') as f:
    f.write(gh)
