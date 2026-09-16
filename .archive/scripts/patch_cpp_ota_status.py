import re

with open('src/esp32_sensor_node/src/OtaUpdater.cpp', 'r') as f:
    content = f.read()

# Add ota_status updates
content = content.replace('Serial.println("[OTA] Mengecek versi terbaru di GitHub...");', 'ota_status = "CHECKING_GITHUB";\n    Serial.println("[OTA] Mengecek versi terbaru di GitHub...");')
content = content.replace('Serial.println("[OTA] Anda sudah menggunakan versi terbaru atau sama.");', 'ota_status = "UP_TO_DATE";\n                Serial.println("[OTA] Anda sudah menggunakan versi terbaru atau sama.");')
content = content.replace('Serial.printf("[OTA] Gagal menghubungi GitHub API. Kode: %d\\n", httpCode);', 'ota_status = "ERROR_API_" + String(httpCode);\n        Serial.printf("[OTA] Gagal menghubungi GitHub API. Kode: %d\\n", httpCode);')
content = content.replace('Serial.printf("[OTA] Gagal mengunduh firmware. Kode: %d\\n", httpCode);', 'ota_status = "ERROR_DOWNLOAD_" + String(httpCode);\n        Serial.printf("[OTA] Gagal mengunduh firmware. Kode: %d\\n", httpCode);')
content = content.replace('Serial.println("[OTA] Memulai penulisan ke memori Flash...");', 'ota_status = "DOWNLOADING_v1.1.0";\n        Serial.println("[OTA] Memulai penulisan ke memori Flash...");')
content = content.replace('Serial.println("[OTA] Update selesai! Restarting...");', 'ota_status = "UPDATE_SUCCESS_RESTARTING";\n                        Serial.println("[OTA] Update selesai! Restarting...");')
content = content.replace('Serial.println("[OTA] Update gagal!");', 'ota_status = "ERROR_UPDATE_FAILED";\n                        Serial.println("[OTA] Update gagal!");')

with open('src/esp32_sensor_node/src/OtaUpdater.cpp', 'w') as f:
    f.write(content)
