import re

with open('src/esp32_sensor_node/src/main.cpp', 'r') as f:
    cpp = f.read()

target_main = '''        if (ota_state == ESP_OTA_IMG_PENDING_VERIFY) {
            Serial.println("[OTA] Firmware baru terdeteksi! Menandai sebagai VALID...");
            esp_ota_mark_app_valid_cancel_rollback();
        }'''

replacement_main = '''        if (ota_state == ESP_OTA_IMG_PENDING_VERIFY) {
            Serial.println("[OTA] Firmware baru terdeteksi! Menandai sebagai VALID...");
            esp_ota_mark_app_valid_cancel_rollback();
            
            // Hapus blacklist karena berhasil boot
            Preferences tempPrefs;
            tempPrefs.begin("ota", false);
            tempPrefs.remove("failed_tag");
            tempPrefs.end();
        }'''

cpp = cpp.replace(target_main, replacement_main)

# Add Preferences.h if not present
if '<Preferences.h>' not in cpp and '"Preferences.h"' not in cpp:
    cpp = cpp.replace('#include "esp_ota_ops.h"', '#include "esp_ota_ops.h"\n#include <Preferences.h>')

with open('src/esp32_sensor_node/src/main.cpp', 'w') as f:
    f.write(cpp)


with open('src/esp32_sensor_node/src/OTAUpdater.cpp', 'r') as f:
    ota = f.read()

# REMOVE the manual esp_ota_set_boot_partition which undoes what Update.end() just did!
target_ota = '''                // Konfigurasi Rollback
                esp_ota_set_boot_partition(esp_ota_get_next_update_partition(NULL));
                return true;'''

replacement_ota = '''                // Update.end() otomatis mengubah boot partition ke firmware baru.
                // JANGAN panggil esp_ota_set_boot_partition() lagi di sini 
                // karena justru akan memutar boot partition kembali ke versi LAMA!
                return true;'''

ota = ota.replace(target_ota, replacement_ota)

with open('src/esp32_sensor_node/src/OTAUpdater.cpp', 'w') as f:
    f.write(ota)

# Bump version
with open('src/esp32_sensor_node/src/OTAUpdater.h', 'r') as f:
    oh = f.read()
oh = oh.replace('#define CURRENT_VERSION "v1.2.3"', '#define CURRENT_VERSION "v1.2.4"')
with open('src/esp32_sensor_node/src/OTAUpdater.h', 'w') as f:
    f.write(oh)

