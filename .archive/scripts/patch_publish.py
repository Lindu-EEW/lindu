import re

with open('src/esp32_sensor_node/src/NetworkManager.cpp', 'r') as f:
    content = f.read()

target = '''    doc["az"]      = az;
    doc["valve_status"] = is_valve_locked ? "DISABLED" : "ENABLED";'''

replace = '''    doc["az"]      = az;
    doc["valve_status"] = is_valve_locked ? "DISABLED" : "ENABLED";
    doc["temperature"] = temp;
    doc["pressure"] = pres;'''

content = content.replace(target, replace)

with open('src/esp32_sensor_node/src/NetworkManager.cpp', 'w') as f:
    f.write(content)
