import re

# 1. Update platformio.ini
pio_content = """[env]
framework = arduino
monitor_speed = 115200
lib_deps =
    madhephaestus/ESP32Servo @ ^1.1.1
    bblanchon/ArduinoJson @ ^6.21.3
    knolleary/PubSubClient @ ^2.8
    adafruit/Adafruit LSM6DS @ ^4.7.0
    adafruit/Adafruit Unified Sensor @ ^1.1.14
    adafruit/Adafruit BME280 Library @ ^2.2.4
    adafruit/Adafruit BMP280 Library @ ^2.6.8
    adafruit/Adafruit NeoPixel @ ^1.11.0
    https://github.com/tzapu/WiFiManager.git

[env:esp32s3]
platform = espressif32
board = esp32-s3-devkitc-1
board_build.arduino.memory_type = qio_opi
board_build.flash_mode = qio
board_build.psram_type = opi
board_upload.flash_size = 8MB
build_flags = 
    -D CORE_DEBUG_LEVEL=3
    -D ARDUINO_USB_CDC_ON_BOOT=1
    -D BOARD_HAS_PSRAM
    -D MQTT_MAX_PACKET_SIZE=1024
    -D PIN_I2C_ATMO_SDA=15
    -D PIN_I2C_ATMO_SCL=16
    -D PIN_I2C_SEIS_SDA=12
    -D PIN_I2C_SEIS_SCL=13

[env:esp32_wroom]
platform = espressif32
board = esp32dev
build_flags = 
    -D CORE_DEBUG_LEVEL=3
    -D MQTT_MAX_PACKET_SIZE=1024
    -D PIN_I2C_ATMO_SDA=21
    -D PIN_I2C_ATMO_SCL=22
    -D PIN_I2C_SEIS_SDA=18
    -D PIN_I2C_SEIS_SCL=19
"""
with open('src/esp32_sensor_node/platformio.ini', 'w') as f:
    f.write(pio_content)

# 2. Update SensorManager.cpp
with open('src/esp32_sensor_node/src/SensorManager.cpp', 'r') as f:
    sm = f.read()
sm = sm.replace('Wire.begin(12, 13);', 'Wire.begin(PIN_I2C_SEIS_SDA, PIN_I2C_SEIS_SCL);')
sm = sm.replace('Wire1.begin(15, 16);', 'Wire1.begin(PIN_I2C_ATMO_SDA, PIN_I2C_ATMO_SCL);')
with open('src/esp32_sensor_node/src/SensorManager.cpp', 'w') as f:
    f.write(sm)

# 3. Update ota_release.yml
with open('src/esp32_sensor_node/.github/workflows/ota_release.yml', 'r') as f:
    yml = f.read()

yml = yml.replace('pio run -e esp32s3', 'pio run')
yml = yml.replace('mv .pio/build/esp32s3/firmware.bin firmware_esp32s3.bin', 
                  'mv .pio/build/esp32s3/firmware.bin firmware_esp32s3.bin\n          mv .pio/build/esp32_wroom/firmware.bin firmware_esp32_wroom.bin')
yml = yml.replace('files: firmware_esp32s3.bin', 'files: firmware_*.bin')

with open('src/esp32_sensor_node/.github/workflows/ota_release.yml', 'w') as f:
    f.write(yml)

# 4. Bump version to v1.1.25
with open('src/esp32_sensor_node/src/OTAUpdater.h', 'r') as f:
    oh = f.read()
oh = oh.replace('#define CURRENT_VERSION "v1.1.24"', '#define CURRENT_VERSION "v1.1.25"')
with open('src/esp32_sensor_node/src/OTAUpdater.h', 'w') as f:
    f.write(oh)

