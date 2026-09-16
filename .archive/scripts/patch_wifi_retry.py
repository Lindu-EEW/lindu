with open('src/esp32_sensor_node/src/main.cpp', 'r') as f:
    cpp = f.read()

# =====================================================
# FIX 1: Tambah retry WiFi sebelum masuk Captive Portal
# Jika WiFi credentials sudah tersimpan, coba konek 3x
# sebelum menyerah dan membuka AP mode
# =====================================================
target_portal = '''    Serial.println("[i] Memulai koneksi WiFi / Captive Portal...");
    if (!configMgr.startCaptivePortal()) {
        Serial.println("[!] Gagal connect WiFi. Alat akan restart...");
        delay(3000);
        ESP.restart();
    }
    Serial.println("[OK] WiFi Terhubung.");'''

replacement_portal = '''    Serial.println("[i] Memulai koneksi WiFi...");
    
    // RETRY LOGIC: Coba koneksi WiFi 3x sebelum masuk Captive Portal
    // Ini mengatasi masalah pasca-OTA reboot dimana router belum siap
    bool wifi_ok = false;
    for (int attempt = 1; attempt <= 3; attempt++) {
        Serial.printf("[WiFi] Percobaan %d/3...\\n", attempt);
        WiFi.begin(); // Gunakan kredensial tersimpan
        
        unsigned long start = millis();
        while (WiFi.status() != WL_CONNECTED && millis() - start < 10000) {
            delay(500);
            Serial.print(".");
            pixels.setPixelColor(0, (millis() / 300) % 2 ? pixels.Color(0, 0, 40) : pixels.Color(0, 0, 0));
            pixels.show();
        }
        Serial.println();
        
        if (WiFi.status() == WL_CONNECTED) {
            wifi_ok = true;
            Serial.println("[OK] WiFi Terhubung via kredensial tersimpan!");
            break;
        }
        Serial.printf("[!] Gagal percobaan %d. Menunggu 3 detik...\\n", attempt);
        delay(3000);
    }
    
    // Jika 3x retry gagal, baru buka Captive Portal sebagai fallback
    if (!wifi_ok) {
        Serial.println("[i] Retry habis. Membuka Captive Portal...");
        if (!configMgr.startCaptivePortal()) {
            Serial.println("[!] Gagal connect WiFi. Alat akan restart...");
            delay(3000);
            ESP.restart();
        }
    }
    Serial.println("[OK] WiFi Terhubung.");'''

cpp = cpp.replace(target_portal, replacement_portal)

with open('src/esp32_sensor_node/src/main.cpp', 'w') as f:
    f.write(cpp)

# =====================================================
# FIX 2: Tambah WiFi auto-reconnect di NetworkManager
# Jika WiFi putus saat runtime, coba sambungkan kembali
# =====================================================
with open('src/esp32_sensor_node/src/NetworkManager.cpp', 'r') as f:
    nm = f.read()

target_loop = '''void NetworkManager::loop() {
    if (!mqtt.connected()) {
        reconnectMQTT();
    }
    mqtt.loop();
}'''

replacement_loop = '''void NetworkManager::loop() {
    // AUTO-RECONNECT WiFi jika terputus saat runtime
    if (WiFi.status() != WL_CONNECTED) {
        static unsigned long last_wifi_retry = 0;
        if (millis() - last_wifi_retry > 10000) { // Retry setiap 10 detik
            last_wifi_retry = millis();
            Serial.println("[WiFi] Koneksi terputus! Mencoba reconnect...");
            WiFi.disconnect();
            WiFi.begin(); // Gunakan kredensial tersimpan
        }
        return; // Jangan coba MQTT jika WiFi belum konek
    }
    
    if (!mqtt.connected()) {
        reconnectMQTT();
    }
    mqtt.loop();
}'''

nm = nm.replace(target_loop, replacement_loop)

with open('src/esp32_sensor_node/src/NetworkManager.cpp', 'w') as f:
    f.write(nm)

# Bump version
with open('src/esp32_sensor_node/src/OTAUpdater.h', 'r') as f:
    oh = f.read()
oh = oh.replace('#define CURRENT_VERSION "v1.2.1"', '#define CURRENT_VERSION "v1.2.2"')
with open('src/esp32_sensor_node/src/OTAUpdater.h', 'w') as f:
    f.write(oh)

