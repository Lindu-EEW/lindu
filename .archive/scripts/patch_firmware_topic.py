with open('src/esp32_sensor_node/src/NetworkManager.cpp', 'r') as f:
    code = f.read()

target_str = 'mqtt.subscribe("lindu/actuator/cmd/all", 1);'
replacement_str = '''// Subscribe ke topik sensor spesifik dan global
            String my_id = String(_configMgr->config.node_id);
            mqtt.subscribe("lindu/sensor/cmd/all", 1);
            mqtt.subscribe(("lindu/sensor/cmd/" + my_id).c_str(), 1);
            // Tetap subscribe ke topik lama demi kompatibilitas mundur jika ada
            mqtt.subscribe("lindu/actuator/cmd/all", 1);'''

code = code.replace(target_str, replacement_str)

with open('src/esp32_sensor_node/src/NetworkManager.cpp', 'w') as f:
    f.write(code)

