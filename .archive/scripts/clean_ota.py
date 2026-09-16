import re

with open('src/esp32_sensor_node/src/OTAUpdater.cpp', 'r') as f:
    cpp = f.read()

target = '''    // Check if we just booted from a rollback
    esp_ota_img_states_t ota_state;
    if (esp_ota_get_state_partition(esp_ota_get_running_partition(), &ota_state) == ESP_OK) {
        if (ota_state == ESP_OTA_IMG_PENDING_VERIFY) {
            Serial.println("[OTA] Firmware baru sukses di-boot! Menandai sebagai valid...");
            esp_ota_mark_app_valid_cancel_rollback();
            _prefs.remove("failed_tag"); // Hapus blacklist karena berhasil boot
        }
    }'''

replacement = '''    // Validasi firmware sekarang dipindah ke baris pertama main.cpp::setup()
    // agar tidak terjadi rollback race condition jika WiFi gagal konek.'''

cpp = cpp.replace(target, replacement)

with open('src/esp32_sensor_node/src/OTAUpdater.cpp', 'w') as f:
    f.write(cpp)
