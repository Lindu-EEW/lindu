import re
with open('src/esp32_sensor_node/src/main.cpp', 'r') as f:
    content = f.read()

# Remove them from inside the block
old_decl = """            bool is_global_alarm = (millis() < global_alarm_until && global_alarm_until > 0);
            bool is_local_alarm = (millis() < local_alarm_until && local_alarm_until > 0);"""
content = content.replace(old_decl, "")

# Add them right before the WiFi check block
old_wifi = "        // Animasi LED Cerdas (Sesuai Status Sensor & WiFi)"
new_wifi = """        // Cek status alarm global dan lokal
        bool is_global_alarm = (millis() < global_alarm_until && global_alarm_until > 0);
        bool is_local_alarm = (millis() < local_alarm_until && local_alarm_until > 0);
        
        // Animasi LED Cerdas (Sesuai Status Sensor & WiFi)"""
content = content.replace(old_wifi, new_wifi)

with open('src/esp32_sensor_node/src/main.cpp', 'w') as f:
    f.write(content)
