import re

with open('src/esp32_sensor_node/src/NetworkManager.cpp', 'r') as f:
    content = f.read()

old_event = """    doc["ay"]      = ay;
    doc["az"]      = az;
    
    // Data Cuaca (Hanya diisi jika valid)"""

new_event = """    doc["ay"]      = ay;
    doc["az"]      = az;
    doc["valve_status"] = is_valve_locked ? "DISABLED" : "ENABLED";
    
    // Data Cuaca (Hanya diisi jika valid)"""

content = content.replace(old_event, new_event)

with open('src/esp32_sensor_node/src/NetworkManager.cpp', 'w') as f:
    f.write(content)
