with open('src/esp32_sensor_node/src/main.cpp', 'r') as f:
    cpp = f.read()

target_led = '''            } else if (is_local_alarm) {
                // DETEKSI GETARAN LOKAL (Menunggu Konfirmasi Node Lain): HANYA Berkedip Pink
                if ((millis() / 500) % 2 == 0) {
                    pixels.setPixelColor(0, pixels.Color(255, 20, 147)); // Hot Pink
                } else {
                    pixels.setPixelColor(0, pixels.Color(0, 0, 0));
                    digitalWrite(BUZZER_PIN, HIGH);
                }} else if (!sensorMgr.sensor_ok && !hw611_ok) {'''

replacement_led = '''            } else if (is_local_alarm) {
                // DETEKSI GETARAN LOKAL (Menunggu Konfirmasi Node Lain): HANYA Berkedip Pink
                if ((millis() / 500) % 2 == 0) {
                    pixels.setPixelColor(0, pixels.Color(255, 20, 147)); // Hot Pink
                } else {
                    pixels.setPixelColor(0, pixels.Color(0, 0, 0));
                    digitalWrite(BUZZER_PIN, HIGH);
                }
            } else if (otaUpdater.ota_status == "DOWNLOADING_FIRMWARE" || otaUpdater.ota_status == "CHECKING_GITHUB") {
                // OTA SEDANG MENGUNDUH: Berkedip Kuning/Oranye sangat cepat layaknya loading
                if ((millis() / 80) % 2 == 0) pixels.setPixelColor(0, pixels.Color(255, 120, 0));
                else pixels.setPixelColor(0, pixels.Color(0, 0, 0));
            } else if (otaUpdater.ota_status == "UPDATE_SUCCESS_RESTARTING") {
                // OTA SELESAI & SIAP RESTART: Menyala Ungu Solid
                pixels.setPixelColor(0, pixels.Color(128, 0, 128));
            } else if (!sensorMgr.sensor_ok && !hw611_ok) {'''

cpp = cpp.replace(target_led, replacement_led)

with open('src/esp32_sensor_node/src/main.cpp', 'w') as f:
    f.write(cpp)

# Bump version
with open('src/esp32_sensor_node/src/OTAUpdater.h', 'r') as f:
    oh = f.read()
oh = oh.replace('#define CURRENT_VERSION "v1.2.5"', '#define CURRENT_VERSION "v1.2.6"')
with open('src/esp32_sensor_node/src/OTAUpdater.h', 'w') as f:
    f.write(oh)

