import sys

with open('src/esp32_sensor_node/src/main.cpp', 'r') as f:
    content = f.read()

# Fix the buzzer not turning off when entering OTA mode
old_block = """            } else if (otaUpdater.ota_status == "DOWNLOADING_FIRMWARE" || otaUpdater.ota_status == "CHECKING_GITHUB") {
                // OTA SEDANG MENGUNDUH: Berkedip CYAN (Biru Tosca) sangat cepat layaknya loading
                if ((millis() / 80) % 2 == 0) pixels.setPixelColor(0, pixels.Color(0, 255, 255));
                else pixels.setPixelColor(0, pixels.Color(0, 0, 0));
            } else if (otaUpdater.ota_status == "UPDATE_SUCCESS_RESTARTING") {"""

new_block = """            } else if (otaUpdater.ota_status == "DOWNLOADING_FIRMWARE" || otaUpdater.ota_status == "CHECKING_GITHUB") {
                // MATIKAN BUZZER JIKA SEBELUMNYA NYALA
                analogWrite(BUZZER_PIN, 255); digitalWrite(BUZZER_PIN, HIGH);
                
                // OTA SEDANG MENGUNDUH: Berkedip CYAN (Biru Tosca) sangat cepat layaknya loading
                if ((millis() / 80) % 2 == 0) pixels.setPixelColor(0, pixels.Color(0, 255, 255));
                else pixels.setPixelColor(0, pixels.Color(0, 0, 0));
            } else if (otaUpdater.ota_status == "UPDATE_SUCCESS_RESTARTING") {"""

content = content.replace(old_block, new_block)

with open('src/esp32_sensor_node/src/main.cpp', 'w') as f:
    f.write(content)

