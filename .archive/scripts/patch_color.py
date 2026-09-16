with open('src/esp32_sensor_node/src/main.cpp', 'r') as f:
    cpp = f.read()

target = '''            } else if (otaUpdater.ota_status == "DOWNLOADING_FIRMWARE" || otaUpdater.ota_status == "CHECKING_GITHUB") {
                // OTA SEDANG MENGUNDUH: Berkedip Kuning/Oranye sangat cepat layaknya loading
                if ((millis() / 80) % 2 == 0) pixels.setPixelColor(0, pixels.Color(255, 120, 0));'''

replacement = '''            } else if (otaUpdater.ota_status == "DOWNLOADING_FIRMWARE" || otaUpdater.ota_status == "CHECKING_GITHUB") {
                // OTA SEDANG MENGUNDUH: Berkedip CYAN (Biru Tosca) sangat cepat layaknya loading
                if ((millis() / 80) % 2 == 0) pixels.setPixelColor(0, pixels.Color(0, 255, 255));'''

cpp = cpp.replace(target, replacement)

with open('src/esp32_sensor_node/src/main.cpp', 'w') as f:
    f.write(cpp)

# Bump version
with open('src/esp32_sensor_node/src/OTAUpdater.h', 'r') as f:
    oh = f.read()
oh = oh.replace('#define CURRENT_VERSION "v1.2.6"', '#define CURRENT_VERSION "v1.2.7"')
with open('src/esp32_sensor_node/src/OTAUpdater.h', 'w') as f:
    f.write(oh)

