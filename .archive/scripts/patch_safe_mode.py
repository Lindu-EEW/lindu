import re

with open('src/esp32_sensor_node/src/main.cpp', 'r') as f:
    content = f.read()

rtc_code = '''
#include <Adafruit_NeoPixel.h>

// --- RESCUE MODE (SAFE MODE) VARIABLES ---
// RTC memory bertahan saat ESP32 crash atau reboot
RTC_DATA_ATTR int boot_crash_count = 0;
bool is_rescue_mode = false;
'''

content = content.replace('#include <Adafruit_NeoPixel.h>', rtc_code)

setup_target = '''void setup() {
    Serial.begin(115200);
    delay(1000);'''

setup_replace = '''void setup() {
    Serial.begin(115200);
    delay(1000);

    boot_crash_count++;
    Serial.printf("[BOOT] Boot/Crash Count: %d\\n", boot_crash_count);
    
    if (boot_crash_count >= 3) {
        Serial.println("=================================================");
        Serial.println("🚨 RESCUE MODE AKTIF 🚨");
        Serial.println("Sistem mendeteksi 3x crash beruntun saat booting.");
        Serial.println("Mematikan semua sensor, I2C, dan Task...");
        Serial.println("=================================================");
        is_rescue_mode = true;
    }
'''

content = content.replace(setup_target, setup_replace)

network_task_target = '''        // 1. Eksekusi Jaringan & OTA Update
        networkMgr.loop();
        otaUpdater.loop();'''

network_task_replace = '''        // 1. Eksekusi Jaringan & OTA Update
        networkMgr.loop();
        otaUpdater.loop();
        
        // Reset crash counter setelah 30 detik hidup stabil
        if (millis() > 30000 && boot_crash_count > 0) {
            boot_crash_count = 0;
            Serial.println("[SYSTEM] Sistem stabil. Boot crash counter di-reset.");
        }
'''

content = content.replace(network_task_target, network_task_replace)

sensor_begin_target = '''    // 3. Inisialisasi Sensor (Hanya di Core 1)
    sensorMgr.begin();'''

sensor_begin_replace = '''    // 3. Inisialisasi Sensor (Bypass jika Rescue Mode)
    if (!is_rescue_mode) {
        sensorMgr.begin();
    } else {
        Serial.println("[RESCUE] Bypass inisialisasi sensor hardware.");
    }'''

content = content.replace(sensor_begin_target, sensor_begin_replace)

sensor_task_target = '''    while (true) {
        sensorMgr.loop();
        
        // Ambil data dari sensor
        SensorData data = sensorMgr.getData();'''

sensor_task_replace = '''    while (true) {
        if (!is_rescue_mode) {
            sensorMgr.loop();
        }
        
        // Ambil data dari sensor
        SensorData data = sensorMgr.getData();'''

content = content.replace(sensor_task_target, sensor_task_replace)

with open('src/esp32_sensor_node/src/main.cpp', 'w') as f:
    f.write(content)
