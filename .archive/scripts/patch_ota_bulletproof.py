import re

with open('src/esp32_sensor_node/src/OtaUpdater.cpp', 'r') as f:
    content = f.read()

target = '''        String payload = http.getString();
        DynamicJsonDocument doc(8192);
        DeserializationError error = deserializeJson(doc, payload);'''

replacement = '''        // [BULLETPROOF] Menggunakan Stream dan Filter agar hemat RAM (anti-crash walau JSON GitHub raksasa)
        StaticJsonDocument<200> filter;
        filter["tag_name"] = true;
        
        DynamicJsonDocument doc(1024);
        DeserializationError error = deserializeJson(doc, http.getStream(), DeserializationOption::Filter(filter));'''

content = content.replace(target, replacement)

with open('src/esp32_sensor_node/src/OtaUpdater.cpp', 'w') as f:
    f.write(content)
