import re
with open('src/esp32_sensor_node/platformio.ini', 'r') as f:
    content = f.read()

if "ESP32Servo" not in content:
    content = content.replace("lib_deps =", "lib_deps =\n    madhephaestus/ESP32Servo @ ^1.1.1")

with open('src/esp32_sensor_node/platformio.ini', 'w') as f:
    f.write(content)
