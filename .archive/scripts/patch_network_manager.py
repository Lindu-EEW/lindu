import re

with open('src/esp32_sensor_node/src/NetworkManager.h', 'r') as f:
    content = f.read()

if "extern bool is_global_alarm;" not in content:
    content = content + "\nextern bool is_global_alarm;\nextern unsigned long global_alarm_until;\n"

with open('src/esp32_sensor_node/src/NetworkManager.h', 'w') as f:
    f.write(content)

with open('src/esp32_sensor_node/src/NetworkManager.cpp', 'r') as f:
    content = f.read()

old_logic = """            if (dist < 50.0) {
                Serial.println("[!] SIRINE MENYALA! Epicenter berjarak < 50km.");
            } else {
                Serial.println("[i] Epicenter berjarak " + String(dist) + "km. Sirine abaikan.");
            }"""

new_logic = """            bool is_unprovisioned = (instance->_configMgr->config.lat == 0.0 && instance->_configMgr->config.lon == 0.0);
            if (dist < 50.0 || is_unprovisioned) {
                Serial.println("[!] SIRINE MENYALA! Epicenter berjarak < 50km (atau GPS belum diset).");
                is_global_alarm = true;
                global_alarm_until = millis() + 15000; // Nyala 15 detik
            } else {
                Serial.println("[i] Epicenter berjarak " + String(dist) + "km. Sirine abaikan.");
            }"""

content = content.replace(old_logic, new_logic)

with open('src/esp32_sensor_node/src/NetworkManager.cpp', 'w') as f:
    f.write(content)

