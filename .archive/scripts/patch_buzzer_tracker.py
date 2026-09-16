import re
with open('src/esp32_sensor_node/src/main.cpp', 'r') as f:
    content = f.read()

old_logic = """        // Matikan buzzer sepenuhnya jika kondisi aman
        if (!is_global_alarm && !is_local_alarm) {
            analogWrite(BUZZER_PIN, 0);
        }"""

new_logic = """        // Matikan buzzer sepenuhnya jika kondisi aman (Gunakan State Tracker untuk mencegah glitch PWM)
        static bool is_buzzer_active = false;
        
        if (is_global_alarm || is_local_alarm) {
            is_buzzer_active = true;
        } else {
            if (is_buzzer_active) {
                analogWrite(BUZZER_PIN, 0); 
                pinMode(BUZZER_PIN, OUTPUT);
                digitalWrite(BUZZER_PIN, LOW); // Matikan paksa di level hardware
                is_buzzer_active = false;
            }
        }"""

content = content.replace(old_logic, new_logic)

with open('src/esp32_sensor_node/src/main.cpp', 'w') as f:
    f.write(content)
