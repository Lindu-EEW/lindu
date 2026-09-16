import re

with open('src/esp32_sensor_node/src/NetworkManager.cpp', 'r') as f:
    content = f.read()

old_commands = """        } else if (doc["cmd"] == "reset_valve" || doc["cmd"] == "open_valve" || doc["cmd"] == "enable_valve") {
            String target = doc["target_node"] | "all";
            String my_id = String(instance->_configMgr->config.node_id);
            if (target == "all" || target == my_id) {
                Serial.println("[i] Perintah Manual: Valve DIBUKA (Enable/Reset).");
                is_valve_locked = false;
            } else {
                Serial.println("[i] Perintah diabaikan (Bukan untuk Node ini).");
            }
        } else if (doc["cmd"] == "close_valve" || doc["cmd"] == "disable_valve") {
            String target = doc["target_node"] | "all";
            String my_id = String(instance->_configMgr->config.node_id);
            if (target == "all" || target == my_id) {
                Serial.println("[i] Perintah Manual: Valve DITUTUP (Disable/Lock).");
                is_valve_locked = true;
            } else {
                Serial.println("[i] Perintah diabaikan (Bukan untuk Node ini).");
            }
        }"""

new_commands = """        } else if (doc["cmd"] == "enable_valve") {
            String target = doc["target_node"] | "all";
            String my_id = String(instance->_configMgr->config.node_id);
            if (target == "all" || target == my_id) {
                Serial.println("[i] Perintah Sistem: Valve di-ENABLE (Aliran Dibuka).");
                is_valve_locked = false;
            } else {
                Serial.println("[i] Perintah Enable diabaikan (Bukan untuk Node ini).");
            }
        } else if (doc["cmd"] == "disable_valve") {
            String target = doc["target_node"] | "all";
            String my_id = String(instance->_configMgr->config.node_id);
            if (target == "all" || target == my_id) {
                Serial.println("[i] Perintah Sistem: Valve di-DISABLE (Aliran Ditutup).");
                is_valve_locked = true;
            } else {
                Serial.println("[i] Perintah Disable diabaikan (Bukan untuk Node ini).");
            }
        }"""

content = content.replace(old_commands, new_commands)

with open('src/esp32_sensor_node/src/NetworkManager.cpp', 'w') as f:
    f.write(content)

