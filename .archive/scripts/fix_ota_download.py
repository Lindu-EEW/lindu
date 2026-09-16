import re

# 1. Update platformio.ini to include BOARD_VARIANT
with open('src/esp32_sensor_node/platformio.ini', 'r') as f:
    pio = f.read()
pio = pio.replace('-D MQTT_MAX_PACKET_SIZE=1024\n    -D PIN_I2C_ATMO_SDA=15', '-D MQTT_MAX_PACKET_SIZE=1024\n    -D BOARD_VARIANT=\\"esp32s3\\"\n    -D PIN_I2C_ATMO_SDA=15')
pio = pio.replace('-D MQTT_MAX_PACKET_SIZE=1024\n    -D PIN_I2C_ATMO_SDA=21', '-D MQTT_MAX_PACKET_SIZE=1024\n    -D BOARD_VARIANT=\\"esp32_wroom\\"\n    -D PIN_I2C_ATMO_SDA=21')
with open('src/esp32_sensor_node/platformio.ini', 'w') as f:
    f.write(pio)

# 2. Update OTAUpdater.cpp
with open('src/esp32_sensor_node/src/OTAUpdater.cpp', 'r') as f:
    ota = f.read()

target = '''                    if (name.endsWith(".bin")) {
                        bin_url = asset["browser_download_url"].as<String>();
                        break;
                    }'''
replacement = '''                    if (name.endsWith(".bin") && name.indexOf(BOARD_VARIANT) >= 0) {
                        bin_url = asset["browser_download_url"].as<String>();
                        break;
                    }'''
ota = ota.replace(target, replacement)
with open('src/esp32_sensor_node/src/OTAUpdater.cpp', 'w') as f:
    f.write(ota)

# 3. Bump version to v1.1.26
with open('src/esp32_sensor_node/src/OTAUpdater.h', 'r') as f:
    oh = f.read()
oh = oh.replace('#define CURRENT_VERSION "v1.1.25"', '#define CURRENT_VERSION "v1.1.26"')
with open('src/esp32_sensor_node/src/OTAUpdater.h', 'w') as f:
    f.write(oh)

