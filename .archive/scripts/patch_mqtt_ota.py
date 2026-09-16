import re

with open('src/esp32_sensor_node/src/NetworkManager.cpp', 'r') as f:
    content = f.read()

old_cmd = """        } else if (doc["cmd"] == "disable_valve") {
            String target = doc["target_node"] | "all";
            String my_id = String(instance->_configMgr->config.node_id);
            if (target == "all" || target == my_id) {
                Serial.println("[i] Perintah Sistem: Valve di-DISABLE (Aliran Ditutup).");
                is_valve_locked = true;
            } else {
                Serial.println("[i] Perintah Disable diabaikan (Bukan untuk Node ini).");
            }
        }"""

new_cmd = """        } else if (doc["cmd"] == "disable_valve") {
            String target = doc["target_node"] | "all";
            String my_id = String(instance->_configMgr->config.node_id);
            if (target == "all" || target == my_id) {
                Serial.println("[i] Perintah Sistem: Valve di-DISABLE (Aliran Ditutup).");
                is_valve_locked = true;
            } else {
                Serial.println("[i] Perintah Disable diabaikan (Bukan untuk Node ini).");
            }
        } else if (doc["cmd"] == "force_update" || doc["cmd"] == "reboot") {
            String target = doc["target_node"] | "all";
            String my_id = String(instance->_configMgr->config.node_id);
            if (target == "all" || target == my_id) {
                Serial.println("[i] Perintah Sistem: FORCE UPDATE. Restarting ESP32 untuk menarik OTA dari GitHub...");
                delay(1000);
                ESP.restart();
            }
        }"""

content = content.replace(old_cmd, new_cmd)

with open('src/esp32_sensor_node/src/NetworkManager.cpp', 'w') as f:
    f.write(content)

