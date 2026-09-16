import re

with open('src/esp32_sensor_node/src/NetworkManager.cpp', 'r') as f:
    nm = f.read()

target = '''        } else if (doc["cmd"] == "factory_reset") {'''
replacement = '''        } else if (doc["cmd"] == "set_location") {
            String target = doc["target_node"] | "all";
            String my_id = String(instance->_configMgr->config.node_id);
            if (target == "all" || target == my_id) {
                if (doc.containsKey("lat") && doc.containsKey("lon")) {
                    instance->_configMgr->config.lat = doc["lat"];
                    instance->_configMgr->config.lon = doc["lon"];
                    instance->_configMgr->saveConfig();
                    Serial.println("[i] Perintah Sistem: SET LOCATION. Koordinat diperbarui!");
                    instance->forcePublishStatus(); // Segera kirim update ke dashboard
                }
            }
        } else if (doc["cmd"] == "factory_reset") {'''

if "set_location" not in nm:
    nm = nm.replace(target, replacement)
    with open('src/esp32_sensor_node/src/NetworkManager.cpp', 'w') as f:
        f.write(nm)

# Bump version to 1.1.14
with open('src/esp32_sensor_node/src/OTAUpdater.h', 'r') as f:
    oh = f.read()
oh = oh.replace('#define CURRENT_VERSION "v1.1.13"', '#define CURRENT_VERSION "v1.1.14"')
with open('src/esp32_sensor_node/src/OTAUpdater.h', 'w') as f:
    f.write(oh)
