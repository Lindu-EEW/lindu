import re

with open('src/esp32_sensor_node/platformio.ini', 'r') as f:
    content = f.read()

content = content.replace("-D BOARD_HAS_PSRAM", "-D BOARD_HAS_PSRAM\n    -D MQTT_MAX_PACKET_SIZE=1024")

with open('src/esp32_sensor_node/platformio.ini', 'w') as f:
    f.write(content)

print("PlatformIO Patched")
