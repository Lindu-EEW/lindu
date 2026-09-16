import re

with open('src/esp32_sensor_node/src/OtaUpdater.cpp', 'r') as f:
    content = f.read()

# Fix setCACert to setInsecure everywhere
content = content.replace("client.setCACert(rootCACertificate);", "client.setInsecure();")

# Fix failed_tag clearing inside begin()
old_begin = """    if (esp_ota_get_state_partition(esp_ota_get_running_partition(), &ota_state) == ESP_OK) {
        if (ota_state == ESP_OTA_IMG_PENDING_VERIFY) {
            Serial.println("[OTA] Firmware baru sukses di-boot! Menandai sebagai valid...");
            esp_ota_mark_app_valid_cancel_rollback();
        }
    }"""
new_begin = """    if (esp_ota_get_state_partition(esp_ota_get_running_partition(), &ota_state) == ESP_OK) {
        if (ota_state == ESP_OTA_IMG_PENDING_VERIFY) {
            Serial.println("[OTA] Firmware baru sukses di-boot! Menandai sebagai valid...");
            esp_ota_mark_app_valid_cancel_rollback();
            _prefs.remove("failed_tag"); // Hapus blacklist karena berhasil boot
        }
    }"""
content = content.replace(old_begin, new_begin)

with open('src/esp32_sensor_node/src/OtaUpdater.cpp', 'w') as f:
    f.write(content)
