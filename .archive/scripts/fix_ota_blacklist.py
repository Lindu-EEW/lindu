import re

with open('src/esp32_sensor_node/src/OtaUpdater.cpp', 'r') as f:
    content = f.read()

old_logic = """                    Serial.println("[OTA] Ditemukan file .bin! Mengunduh dari: " + bin_url);
                    // Kita akan menandai failed_tag SEBELUM update. 
                    // Jika update sukses dan berhasil boot, kita akan hapus failed_tag ini di begin() firmware baru.
                    // Tapi karena firmware baru yang punya begin(), firmware lama hanya bisa set flag.
                    _prefs.putString("failed_tag", latest_tag); 
                    
                    if (performUpdate(bin_url.c_str(), latest_tag.c_str())) {"""

new_logic = """                    Serial.println("[OTA] Ditemukan file .bin! Mengunduh dari: " + bin_url);
                    
                    if (performUpdate(bin_url.c_str(), latest_tag.c_str())) {
                        // Kita akan menandai failed_tag SETELAH download sukses tapi SEBELUM reboot. 
                        // Jika firmware baru gagal boot (crash), dia akan rollback dan blacklist ini tetap ada.
                        // Jika sukses boot, firmware baru akan menghapus blacklist ini di begin().
                        _prefs.putString("failed_tag", latest_tag);"""

content = content.replace(old_logic, new_logic)

with open('src/esp32_sensor_node/src/OtaUpdater.cpp', 'w') as f:
    f.write(content)
