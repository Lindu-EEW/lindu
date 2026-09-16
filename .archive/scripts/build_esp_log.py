import re

# ==========================================
# 3. TAMBAHKAN PUBLISH_LOG KE ESP32 C++
# ==========================================

# A. NetworkManager.h
with open('src/esp32_sensor_node/src/NetworkManager.h', 'r') as f:
    nmh = f.read()

target_nmh = '''    void publishEvent(double epoch, float pga, float sta_lta, float freq, float ax, float ay, float az, float lat, float lon, float uptime_ms);'''
replacement_nmh = target_nmh + '''\n    void publishLog(const char* message);'''
nmh = nmh.replace(target_nmh, replacement_nmh)
with open('src/esp32_sensor_node/src/NetworkManager.h', 'w') as f:
    f.write(nmh)


# B. NetworkManager.cpp
with open('src/esp32_sensor_node/src/NetworkManager.cpp', 'r') as f:
    nmc = f.read()

log_func = '''void NetworkManager::publishLog(const char* message) {
    if (!mqtt.connected()) return;
    char topic[64];
    snprintf(topic, sizeof(topic), "lindu/sensor/%s/log", _configMgr->config.node_id);
    
    char payload[256];
    snprintf(payload, sizeof(payload), "{\\"message\\":\\"%s\\"}", message);
    
    mqtt.publish(topic, payload, 0, false); // QoS 0, no retain for logs
}
'''
nmc += '\n' + log_func

with open('src/esp32_sensor_node/src/NetworkManager.cpp', 'w') as f:
    f.write(nmc)


# C. main.cpp (Sisipkan publishLog di beberapa momen krusial)
with open('src/esp32_sensor_node/src/main.cpp', 'r') as f:
    cpp = f.read()

cpp = cpp.replace('Serial.println("[OK] WiFi Terhubung via kredensial tersimpan!");', 
                  'Serial.println("[OK] WiFi Terhubung via kredensial tersimpan!");\n            networkMgr.publishLog("WiFi Terhubung (Kredensial Tersimpan).");')

cpp = cpp.replace('Serial.println("[i] Retry habis. Membuka Captive Portal...");',
                  'Serial.println("[i] Retry habis. Membuka Captive Portal...");\n        networkMgr.publishLog("Gagal WiFi 3x, Membuka Captive Portal.");')

cpp = cpp.replace('Serial.println("[!!!] LONE WOLF MODE: Server offline + PGA EKSTREM! Mengambil alih kendali!");',
                  'Serial.println("[!!!] LONE WOLF MODE: Server offline + PGA EKSTREM! Mengambil alih kendali!");\n                    networkMgr.publishLog("LONE WOLF MODE DIINTIASI! Server Offline & PGA Ekstrem.");')

with open('src/esp32_sensor_node/src/main.cpp', 'w') as f:
    f.write(cpp)


# D. OTAUpdater.cpp (Sisipkan log saat OTA)
with open('src/esp32_sensor_node/src/OTAUpdater.cpp', 'r') as f:
    ota = f.read()

ota = ota.replace('Serial.println("[OTA] Ditemukan file .bin! Mengunduh dari: " + bin_url);',
                  'Serial.println("[OTA] Ditemukan file .bin! Mengunduh dari: " + bin_url);\n                    networkMgr.publishLog(("Mengunduh Firmware dari: " + bin_url).c_str());')

ota = ota.replace('Serial.println("[OTA] Update selesai! Restarting...");',
                  'Serial.println("[OTA] Update selesai! Restarting...");\n                        networkMgr.publishLog("OTA Sukses! Alat segera di-restart.");')

with open('src/esp32_sensor_node/src/OTAUpdater.cpp', 'w') as f:
    f.write(ota)

# Bump version to v1.2.9
with open('src/esp32_sensor_node/src/OTAUpdater.h', 'r') as f:
    oh = f.read()
oh = oh.replace('#define CURRENT_VERSION "v1.2.8"', '#define CURRENT_VERSION "v1.2.9"')
with open('src/esp32_sensor_node/src/OTAUpdater.h', 'w') as f:
    f.write(oh)

