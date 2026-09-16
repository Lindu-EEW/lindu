import re
import os

with open('src/esp32_sensor_node/src/NetworkManager.cpp', 'r') as f:
    nm = f.read()

# 1. Zero-Heap Fragmentation in publishStatus
target_publishStatus = '''void NetworkManager::publishStatus(String status, bool sensor_ok, float tilt_angle, String pose) {
    if (!mqtt.connected()) return;
    String willTopic = "lindu/sensor/" + String(_configMgr->config.node_id) + "/status";
    String statusPayload = "{\\"status\\":\\"" + status + "\\",\\"node_id\\":\\"" + String(_configMgr->config.node_id) + "\\",\\"lat\\":" + String(_configMgr->config.lat, 4) + ",\\"lon\\":" + String(_configMgr->config.lon, 4) + ",\\"pose\\":\\"" + pose + "\\",\\"tilt_angle\\":" + String(tilt_angle, 1) + ",\\"sensor_ok\\":" + String(sensor_ok ? "true" : "false") + ",\\"fw_version\\":\\"" + String(CURRENT_VERSION) + "\\",\\"ota_status\\":\\"" + otaUpdater.ota_status + "\\"}";
    mqtt.publish(willTopic.c_str(), statusPayload.c_str(), true);
}'''

replacement_publishStatus = '''void NetworkManager::publishStatus(String status, bool sensor_ok, float tilt_angle, String pose) {
    if (!mqtt.connected()) return;
    char willTopic[64];
    snprintf(willTopic, sizeof(willTopic), "lindu/sensor/%s/status", _configMgr->config.node_id);
    
    char statusPayload[512];
    snprintf(statusPayload, sizeof(statusPayload), 
        "{\\"status\\":\\"%s\\",\\"node_id\\":\\"%s\\",\\"lat\\":%.4f,\\"lon\\":%.4f,\\"pose\\":\\"%s\\",\\"tilt_angle\\":%.1f,\\"sensor_ok\\":%s,\\"fw_version\\":\\"%s\\",\\"ota_status\\":\\"%s\\"}",
        status.c_str(), _configMgr->config.node_id, _configMgr->config.lat, _configMgr->config.lon, pose.c_str(), tilt_angle, sensor_ok ? "true" : "false", CURRENT_VERSION, otaUpdater.ota_status.c_str());
        
    mqtt.publish(willTopic, statusPayload, true);
}'''
nm = nm.replace(target_publishStatus, replacement_publishStatus)


# 2. Zero-Heap Fragmentation in connect block
target_connect = '''        String willTopic = "lindu/sensor/" + String(_configMgr->config.node_id) + "/status";
        String willPayload = "{\\"status\\":\\"offline\\",\\"node_id\\":\\"" + String(_configMgr->config.node_id) + "\\"}";
        
        if (mqtt.connect(_configMgr->config.node_id, willTopic.c_str(), 1, true, willPayload.c_str())) {
            Serial.println("TERHUBUNG KE MQTT!");
            
            String statusPayload = "{\\"status\\":\\"online\\",\\"node_id\\":\\"" + String(_configMgr->config.node_id) + "\\",\\"lat\\":" + String(_configMgr->config.lat, 4) + ",\\"lon\\":" + String(_configMgr->config.lon, 4) + ",\\"pose\\":\\"" + sensorMgr.getPose() + "\\",\\"tilt_angle\\":" + String(sensorMgr.getTiltAngle(), 1) + ",\\"sensor_ok\\":" + String(sensorMgr.sensor_ok ? "true" : "false") + "}";
            mqtt.publish(willTopic.c_str(), statusPayload.c_str(), true);'''

replacement_connect = '''        char willTopic[64];
        snprintf(willTopic, sizeof(willTopic), "lindu/sensor/%s/status", _configMgr->config.node_id);
        
        char willPayload[128];
        snprintf(willPayload, sizeof(willPayload), "{\\"status\\":\\"offline\\",\\"node_id\\":\\"%s\\"}", _configMgr->config.node_id);
        
        if (mqtt.connect(_configMgr->config.node_id, willTopic, 1, true, willPayload)) {
            Serial.println("TERHUBUNG KE MQTT!");
            
            char statusPayload[512];
            snprintf(statusPayload, sizeof(statusPayload), 
                "{\\"status\\":\\"online\\",\\"node_id\\":\\"%s\\",\\"lat\\":%.4f,\\"lon\\":%.4f,\\"pose\\":\\"%s\\",\\"tilt_angle\\":%.1f,\\"sensor_ok\\":%s}",
                _configMgr->config.node_id, _configMgr->config.lat, _configMgr->config.lon, sensorMgr.getPose().c_str(), sensorMgr.getTiltAngle(), sensorMgr.sensor_ok ? "true" : "false");
            mqtt.publish(willTopic, statusPayload, true);'''

nm = nm.replace(target_connect, replacement_connect)

# 3. Topic in publishEvent
nm = nm.replace('String topic = "lindu/sensor/" + String(_configMgr->config.node_id) + "/telemetry";', 
                'char topic[64];\n    snprintf(topic, sizeof(topic), "lindu/sensor/%s/telemetry", _configMgr->config.node_id);')
nm = nm.replace('mqtt.publish(topic.c_str(), buffer);', 'mqtt.publish(topic, buffer);')

with open('src/esp32_sensor_node/src/NetworkManager.cpp', 'w') as f:
    f.write(nm)


# 4. FREE RTOS OTA
with open('src/esp32_sensor_node/src/OTAUpdater.cpp', 'r') as f:
    otac = f.read()

target_loop = '''void OTAUpdater::loop() {
    // Check update every 24 hours (or at boot + 30s)
    if (_last_check == 0 && millis() > 30000) {
        checkForUpdate();
        _last_check = millis();
    } else if (millis() - _last_check > 43200000) { // 12 Jam
        checkForUpdate();
        _last_check = millis();
    }
}'''

replacement_loop = '''
TaskHandle_t otaTaskHandle = NULL;
void otaTask(void *pvParameters) {
    OTAUpdater* updater = (OTAUpdater*)pvParameters;
    updater->checkForUpdate();
    otaTaskHandle = NULL;
    vTaskDelete(NULL);
}

void OTAUpdater::loop() {
    // Check update every 24 hours (or at boot + 30s)
    if ((_last_check == 0 && millis() > 30000) || (millis() - _last_check > 43200000)) {
        _last_check = millis();
        if (otaTaskHandle == NULL) {
            Serial.println("[OTA] Memicu FreeRTOS Background Task di Core 0...");
            xTaskCreatePinnedToCore(otaTask, "OTA_Task", 8192, this, 1, &otaTaskHandle, 0); // Core 0
        }
    }
}'''

otac = otac.replace(target_loop, replacement_loop)

# Fix ESPHTTPUpdate header inclusion to avoid crash if not properly scoped
if "#include <esp_task_wdt.h>" not in otac:
    otac = "#include <esp_task_wdt.h>\n" + otac

with open('src/esp32_sensor_node/src/OTAUpdater.cpp', 'w') as f:
    f.write(otac)

# Bump Version
with open('src/esp32_sensor_node/src/OTAUpdater.h', 'r') as f:
    oh = f.read()
oh = oh.replace('#define CURRENT_VERSION "v1.1.32"', '#define CURRENT_VERSION "v1.1.33"')
with open('src/esp32_sensor_node/src/OTAUpdater.h', 'w') as f:
    f.write(oh)

