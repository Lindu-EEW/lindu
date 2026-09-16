import re

with open('src/esp32_sensor_node/src/main.cpp', 'r') as f:
    content = f.read()

old_logic = """            // LOGIKA VALVE MANUAL RESET
            if (is_valve_locked) {
                myServo.write(90); // Mengunci (Tutup) sampai direset
            } else {
                myServo.write(0);  // Normal (Buka)
            }"""
            
new_logic = """            // LOGIKA VALVE MANUAL RESET (EDGE TRIGGER agar Servo tidak bergetar/buzzer)
            static bool last_valve_state = false;
            if (is_valve_locked != last_valve_state) {
                if (is_valve_locked) {
                    myServo.write(90); // Mengunci (Tutup) sampai direset
                } else {
                    myServo.write(0);  // Normal (Buka)
                }
                last_valve_state = is_valve_locked;
            }"""

content = content.replace(old_logic, new_logic)

with open('src/esp32_sensor_node/src/main.cpp', 'w') as f:
    f.write(content)

print("Servo Spam Patched")
