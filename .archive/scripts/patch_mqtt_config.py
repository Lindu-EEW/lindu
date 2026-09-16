import re

with open('src/esp32_sensor_node/src/ConfigManager.cpp', 'r') as f:
    cfg = f.read()

cfg = cfg.replace('config.is_provisioned = (config.lat != 0.0);', '''
    String srv = prefs.getString("mqtt_srv", "192.168.68.105");
    strlcpy(config.mqtt_server, srv.c_str(), sizeof(config.mqtt_server));
    config.is_provisioned = (config.lat != 0.0);
''')

cfg = cfg.replace('prefs.putFloat("lon", config.lon);', '''prefs.putFloat("lon", config.lon);
    prefs.putString("mqtt_srv", config.mqtt_server);''')

cfg = cfg.replace('WiFiManagerParameter custom_lat', '''WiFiManagerParameter custom_mqtt("mqtt", "MQTT Broker IP/Domain", config.mqtt_server, 64);
    wm.addParameter(&custom_mqtt);
    WiFiManagerParameter custom_lat''')

cfg = cfg.replace('config.lon = atof(custom_lon.getValue());', '''config.lon = atof(custom_lon.getValue());
    strlcpy(config.mqtt_server, custom_mqtt.getValue(), sizeof(config.mqtt_server));''')

with open('src/esp32_sensor_node/src/ConfigManager.cpp', 'w') as f:
    f.write(cfg)

with open('src/esp32_sensor_node/src/NetworkManager.cpp', 'r') as f:
    nm = f.read()

nm = nm.replace('mqtt.setServer("192.168.68.105", 1883);', 'mqtt.setServer(_configMgr->config.mqtt_server, 1883);')

remote_cmd = '''        } else if (doc["cmd"] == "force_update" || doc["cmd"] == "reboot") {'''
new_cmd = '''        } else if (doc["cmd"] == "set_broker") {
            String target = doc["target_node"] | "all";
            String my_id = String(instance->_configMgr->config.node_id);
            if (target == "all" || target == my_id) {
                if (doc.containsKey("server")) {
                    strlcpy(instance->_configMgr->config.mqtt_server, doc["server"].as<const char*>(), 64);
                    instance->_configMgr->saveConfig();
                    Serial.println("[i] Perintah Sistem: SET BROKER. Restarting ESP32...");
                    delay(1000);
                    ESP.restart();
                }
            }
        } else if (doc["cmd"] == "force_update" || doc["cmd"] == "reboot") {'''

nm = nm.replace(remote_cmd, new_cmd)

with open('src/esp32_sensor_node/src/NetworkManager.cpp', 'w') as f:
    f.write(nm)

