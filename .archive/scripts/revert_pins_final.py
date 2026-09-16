import re

# 1. Update platformio.ini to move pins back to 10 & 11
with open('src/esp32_sensor_node/platformio.ini', 'r') as f:
    pio = f.read()

pio = pio.replace('-D PIN_I2C_ATMO_SDA=15\n    -D PIN_I2C_ATMO_SCL=16', '-D PIN_I2C_ATMO_SDA=10\n    -D PIN_I2C_ATMO_SCL=11')

with open('src/esp32_sensor_node/platformio.ini', 'w') as f:
    f.write(pio)

# 2. Bump version to v1.1.30
with open('src/esp32_sensor_node/src/OTAUpdater.h', 'r') as f:
    oh = f.read()

oh = oh.replace('#define CURRENT_VERSION "v1.1.29"', '#define CURRENT_VERSION "v1.1.30"')

with open('src/esp32_sensor_node/src/OTAUpdater.h', 'w') as f:
    f.write(oh)

# 3. Revert DEVELOPMENT_FLOW.md docs
with open('/Users/likotjhang/.gemini/antigravity/brain/a862d96c-2e98-45da-ab7b-39956704063d/DEVELOPMENT_FLOW.md', 'r') as f:
    doc = f.read()

doc = doc.replace('**SDA = 15, SCL = 16** | *Permanently remapped due to hardware defect on pins 10/11.*', '**SDA = 10, SCL = 11** | Pin standar I2C untuk ESP32-S3.')
doc = doc.replace('v1.1.29', 'v1.1.30')

with open('/Users/likotjhang/.gemini/antigravity/brain/a862d96c-2e98-45da-ab7b-39956704063d/DEVELOPMENT_FLOW.md', 'w') as f:
    f.write(doc)

