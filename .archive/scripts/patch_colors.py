import re

with open('src/esp32_sensor_node/src/main.cpp', 'r') as f:
    content = f.read()

target = '''    // 3. Inisialisasi Sensor (Bypass jika Rescue Mode)
    if (!is_rescue_mode) {
        sensorMgr.begin(eventQueue);
    } else {
        Serial.println("[RESCUE] Bypass inisialisasi sensor hardware.");
    }'''

replace = '''    // 3. Inisialisasi Sensor (Bypass jika Rescue Mode)
    if (!is_rescue_mode) {
        sensorMgr.begin(eventQueue);
        
        bool has_accel = sensorMgr.sensor_ok;
        bool has_atmo = sensorMgr.bme_ok || sensorMgr.bmp_ok;
        
        if (has_accel && has_atmo) {
            // HIJAU (2x) = Semua Sensor Terpasang & Sehat
            for(int i=0; i<2; i++) { pixels.setPixelColor(0, pixels.Color(0, 50, 0)); pixels.show(); delay(200); pixels.setPixelColor(0, 0); pixels.show(); delay(200); }
        } else if (has_accel && !has_atmo) {
            // KUNING (2x) = Akselerometer OK, tapi Cuaca (BME/BMP) Terlepas/Mati
            for(int i=0; i<2; i++) { pixels.setPixelColor(0, pixels.Color(50, 50, 0)); pixels.show(); delay(200); pixels.setPixelColor(0, 0); pixels.show(); delay(200); }
        } else {
            // MERAH (5x Cepat) = Kritis! Akselerometer Seismik Tidak Ditemukan!
            for(int i=0; i<5; i++) { pixels.setPixelColor(0, pixels.Color(50, 0, 0)); pixels.show(); delay(100); pixels.setPixelColor(0, 0); pixels.show(); delay(100); }
        }
    } else {
        Serial.println("[RESCUE] Bypass inisialisasi sensor hardware.");
    }'''

content = content.replace(target, replace)

with open('src/esp32_sensor_node/src/main.cpp', 'w') as f:
    f.write(content)
