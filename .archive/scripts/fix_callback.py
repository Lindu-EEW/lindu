import re

with open('src/esp32_sensor_node/src/NetworkManager.cpp', 'r') as f:
    content = f.read()

# Replace the whole mqttCallback
def replacement(match):
    return """void NetworkManager::mqttCallback(char* topic, byte* payload, unsigned int length) {
    String msg;
    for (int i = 0; i < length; i++) msg += (char)payload[i];
    
    if (String(topic) == "lindu/actuator/cmd/all") {
        StaticJsonDocument<256> doc;
        DeserializationError error = deserializeJson(doc, msg);
        if (error) return;
        
        if (doc["cmd"] == "trigger_siren") {
            float e_lat = doc["epicenter_lat"];
            float e_lon = doc["epicenter_lon"];
            
            float dist = instance->haversine(
                instance->_configMgr->config.lat, 
                instance->_configMgr->config.lon, 
                e_lat, e_lon
            );
            
            bool is_unprovisioned = (instance->_configMgr->config.lat == 0.0 && instance->_configMgr->config.lon == 0.0);
            
            if (dist < 50.0 || is_unprovisioned) {
                Serial.println("[!] SIRINE MENYALA! Epicenter berjarak < 50km (Atau Bypass Test).");
                global_alarm_until = millis() + 15000;
            } else {
                Serial.println("[i] Epicenter terlalu jauh. Abaikan.");
            }
        }
    }
}"""

content = re.sub(r'void NetworkManager::mqttCallback.*?\}\s*\}\s*\}', replacement, content, flags=re.DOTALL)

with open('src/esp32_sensor_node/src/NetworkManager.cpp', 'w') as f:
    f.write(content)
