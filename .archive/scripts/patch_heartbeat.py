import re

# 1. Update NetworkManager.h
with open('src/esp32_sensor_node/src/NetworkManager.h', 'r') as f:
    h_content = f.read()
if 'void publishStatus(' not in h_content:
    h_content = h_content.replace('void publishEvent(', 'void publishStatus(String status, bool sensor_ok, float tilt_angle, String pose);\n    void publishEvent(')
with open('src/esp32_sensor_node/src/NetworkManager.h', 'w') as f:
    f.write(h_content)

# 2. Update NetworkManager.cpp
with open('src/esp32_sensor_node/src/NetworkManager.cpp', 'r') as f:
    cpp_content = f.read()

# Extract the payload logic into a new function
new_func = """void NetworkManager::publishStatus(String status, bool sensor_ok, float tilt_angle, String pose) {
    if (!mqtt.connected()) return;
    String willTopic = "lindu/sensor/" + String(_configMgr->config.node_id) + "/status";
    String statusPayload = "{\\"status\\":\\"" + status + "\\",\\"node_id\\":\\"" + String(_configMgr->config.node_id) + "\\",\\"lat\\":" + String(_configMgr->config.lat, 4) + ",\\"lon\\":" + String(_configMgr->config.lon, 4) + ",\\"pose\\":\\"" + pose + "\\",\\"tilt_angle\\":" + String(tilt_angle, 1) + ",\\"sensor_ok\\":" + String(sensor_ok ? "true" : "false") + "}";
    mqtt.publish(willTopic.c_str(), statusPayload.c_str(), true);
}
"""
if 'NetworkManager::publishStatus(' not in cpp_content:
    cpp_content += "\n" + new_func
with open('src/esp32_sensor_node/src/NetworkManager.cpp', 'w') as f:
    f.write(cpp_content)

# 3. Update main.cpp to call it every 10 seconds inside networkTaskCode
with open('src/esp32_sensor_node/src/main.cpp', 'r') as f:
    main_content = f.read()

target_loop = "        networkMgr.loop(); // Handle rutin MQTT"
if "static unsigned long last_status = 0;" not in main_content:
    injection = """        networkMgr.loop(); // Handle rutin MQTT
        
        // Heartbeat status setiap 10 detik
        static unsigned long last_status = 0;
        if (millis() - last_status >= 10000) {
            networkMgr.publishStatus("online", sensorMgr.sensor_ok, sensorMgr.getTiltAngle(), sensorMgr.getPose());
            last_status = millis();
        }"""
    main_content = main_content.replace(target_loop, injection)
with open('src/esp32_sensor_node/src/main.cpp', 'w') as f:
    f.write(main_content)

print("Heartbeat Patched")
