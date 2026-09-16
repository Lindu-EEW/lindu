import re

# 1. Update NetworkManager.cpp
with open('src/esp32_sensor_node/src/NetworkManager.cpp', 'r') as f:
    n_cpp = f.read()

target = '''        } else if (doc["cmd"] == "force_update" || doc["cmd"] == "reboot") {
            String target = doc["target_node"] | "all";
            String my_id = String(instance->_configMgr->config.node_id);
            if (target == "all" || target == my_id) {
                Serial.println("[i] Perintah Sistem: FORCE UPDATE. Restarting ESP32 untuk menarik OTA dari GitHub...");
                delay(1000);'''
replacement = '''        } else if (doc["cmd"] == "force_update" || doc["cmd"] == "reboot") {
            String target = doc["target_node"] | "all";
            String my_id = String(instance->_configMgr->config.node_id);
            if (target == "all" || target == my_id) {
                Serial.println("[i] Perintah Sistem: FORCE UPDATE. Menghapus Blacklist dan Restarting ESP32...");
                Preferences prefs;
                prefs.begin("ota", false);
                prefs.remove("failed_tag");
                prefs.end();
                delay(1000);'''

if "prefs.remove" not in n_cpp:
    n_cpp = n_cpp.replace(target, replacement)
with open('src/esp32_sensor_node/src/NetworkManager.cpp', 'w') as f:
    f.write(n_cpp)

# 2. Update OtaUpdater.cpp
with open('src/esp32_sensor_node/src/OtaUpdater.cpp', 'r') as f:
    o_cpp = f.read()

o_cpp = o_cpp.replace('''                if (latest_tag == _failed_tag) {
                    Serial.println("[OTA] SKIPPED! Versi ini (" + latest_tag + ") pernah membuat sistem crash sebelumnya (Blacklisted).");
                    return;
                }''', '''                if (latest_tag == _failed_tag) {
                    ota_status = "ERROR_BLACKLISTED"; networkMgr.forcePublishStatus();
                    Serial.println("[OTA] SKIPPED! Versi ini (" + latest_tag + ") pernah membuat sistem crash sebelumnya (Blacklisted).");
                    return;
                }''')

# Update CURRENT_VERSION just so it's clean
with open('src/esp32_sensor_node/src/OTAUpdater.h', 'r') as f:
    oh = f.read()
oh = oh.replace('#define CURRENT_VERSION "v1.0.0"', '#define CURRENT_VERSION "v1.1.11"')
with open('src/esp32_sensor_node/src/OTAUpdater.h', 'w') as f:
    f.write(oh)

with open('src/esp32_sensor_node/src/OtaUpdater.cpp', 'w') as f:
    f.write(o_cpp)

