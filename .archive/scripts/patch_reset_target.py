import re

with open('src/esp32_sensor_node/src/NetworkManager.cpp', 'r') as f:
    content = f.read()

old_reset = """        } else if (doc["cmd"] == "reset_valve") {
            Serial.println("[i] Sistem di-Reset Manual. Valve Dibuka.");
            is_valve_locked = false;
        }"""

new_reset = """        } else if (doc["cmd"] == "reset_valve") {
            String target = doc["target_node"] | "all";
            String my_id = String(instance->_configMgr->config.node_id);
            if (target == "all" || target == my_id) {
                Serial.println("[i] Sistem di-Reset Manual. Valve Dibuka.");
                is_valve_locked = false;
            } else {
                Serial.println("[i] Reset diabaikan (Bukan untuk Node ini).");
            }
        }"""

content = content.replace(old_reset, new_reset)

with open('src/esp32_sensor_node/src/NetworkManager.cpp', 'w') as f:
    f.write(content)

print("Reset Target Patched")
