import re

# 1. Update main.cpp
with open('src/esp32_sensor_node/src/main.cpp', 'r') as f:
    m_content = f.read()

# Add identify_until global
if "unsigned long identify_until = 0;" not in m_content:
    m_content = m_content.replace('unsigned long local_alarm_until = 0;', 'unsigned long local_alarm_until = 0;\nunsigned long identify_until = 0;')

# Inject LED logic
old_led_logic = '            if (is_global_alarm) {'
new_led_logic = '''            if (millis() < identify_until) {
                // IDENTIFY MODE: Berkedip Putih
                if ((millis() / 200) % 2 == 0) pixels.setPixelColor(0, pixels.Color(255, 255, 255));
                else pixels.setPixelColor(0, pixels.Color(0, 0, 0));
                digitalWrite(BUZZER_PIN, HIGH);
            } else if (is_global_alarm) {'''
if "IDENTIFY MODE" not in m_content:
    m_content = m_content.replace(old_led_logic, new_led_logic)

with open('src/esp32_sensor_node/src/main.cpp', 'w') as f:
    f.write(m_content)

# 2. Update NetworkManager.cpp
with open('src/esp32_sensor_node/src/NetworkManager.cpp', 'r') as f:
    n_content = f.read()

# Add extern declaration
if "extern unsigned long identify_until;" not in n_content:
    n_content = n_content.replace('#include <math.h>', '#include <math.h>\n\nextern unsigned long identify_until;')

# Add identify command parser
cmd_logic = '''        } else if (doc["cmd"] == "identify") {
            String target = doc["target_node"] | "all";
            String my_id = String(instance->_configMgr->config.node_id);
            if (target == "all" || target == my_id) {
                identify_until = millis() + 10000; // 10 detik
                Serial.println("[i] Perintah Sistem: IDENTIFY. Lampu berkedip putih.");
            }
        } else if (doc["cmd"] == "force_update"'''
if '"cmd"] == "identify"' not in n_content:
    n_content = n_content.replace('        } else if (doc["cmd"] == "force_update"', cmd_logic)

with open('src/esp32_sensor_node/src/NetworkManager.cpp', 'w') as f:
    f.write(n_content)

