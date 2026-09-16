with open('src/esp32_sensor_node/src/main.cpp', 'r') as f:
    cpp = f.read()

# FIX 1: Pindahkan OTA mark_valid ke AWAL setup(), SEBELUM WiFi
# Agar firmware baru tidak di-rollback meskipun WiFi gagal
target_setup = '''    Serial.println("\\n\\n==========================================");
    Serial.println(" Lindu.id - Life-Critical Node v2.0 ");
    Serial.println("==========================================");

    // 1. Muat Konfigurasi (EEPROM) & WiFi Captive Portal
    configMgr.begin();'''

replacement_setup = '''    Serial.println("\\n\\n==========================================");
    Serial.println(" Lindu.id - Life-Critical Node v2.0 ");
    Serial.println("==========================================");

    // 0. SEGERA tandai firmware sebagai VALID agar tidak di-rollback
    // Ini HARUS dilakukan sebelum WiFi agar OTA tidak loop
    esp_ota_img_states_t ota_state;
    if (esp_ota_get_state_partition(esp_ota_get_running_partition(), &ota_state) == ESP_OK) {
        if (ota_state == ESP_OTA_IMG_PENDING_VERIFY) {
            Serial.println("[OTA] Firmware baru terdeteksi! Menandai sebagai VALID...");
            esp_ota_mark_app_valid_cancel_rollback();
        }
    }

    // 1. Muat Konfigurasi (EEPROM) & WiFi Captive Portal
    configMgr.begin();'''

cpp = cpp.replace(target_setup, replacement_setup)

# FIX 2: Gunakan kredensial dari ConfigManager, bukan WiFi.begin() kosong
target_wifi_begin = '''        WiFi.begin(); // Gunakan kredensial tersimpan'''

replacement_wifi_begin = '''        WiFi.begin(configMgr.config.wifi_ssid, configMgr.config.wifi_pass); // Gunakan kredensial dari EEPROM'''

cpp = cpp.replace(target_wifi_begin, replacement_wifi_begin)

# Pastikan include ada
if '#include "esp_ota_ops.h"' not in cpp:
    cpp = cpp.replace('#include <WiFi.h>', '#include <WiFi.h>\n#include "esp_ota_ops.h"')

with open('src/esp32_sensor_node/src/main.cpp', 'w') as f:
    f.write(cpp)

# Bump version
with open('src/esp32_sensor_node/src/OTAUpdater.h', 'r') as f:
    oh = f.read()
oh = oh.replace('#define CURRENT_VERSION "v1.2.2"', '#define CURRENT_VERSION "v1.2.3"')
with open('src/esp32_sensor_node/src/OTAUpdater.h', 'w') as f:
    f.write(oh)

