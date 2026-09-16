import re

# 1. Update platformio.ini to move pins to 15 & 16
with open('src/esp32_sensor_node/platformio.ini', 'r') as f:
    pio = f.read()

pio = pio.replace('-D PIN_I2C_ATMO_SDA=10\n    -D PIN_I2C_ATMO_SCL=11', '-D PIN_I2C_ATMO_SDA=15\n    -D PIN_I2C_ATMO_SCL=16')

with open('src/esp32_sensor_node/platformio.ini', 'w') as f:
    f.write(pio)

# 2. Bump version to v1.1.29
with open('src/esp32_sensor_node/src/OTAUpdater.h', 'r') as f:
    oh = f.read()

oh = oh.replace('#define CURRENT_VERSION "v1.1.28"', '#define CURRENT_VERSION "v1.1.29"')

with open('src/esp32_sensor_node/src/OTAUpdater.h', 'w') as f:
    f.write(oh)

