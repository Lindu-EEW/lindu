import re

with open('src/esp32_sensor_node/src/main.cpp', 'r') as f:
    content = f.read()

# Replace sweeping logic with solid valve logic
old_logic = """                // Ayunkan Servo Kiri-Kanan
                int servo_angle = (millis() / 200) % 2 == 0 ? 90 : 0;
                myServo.write(servo_angle);"""

new_logic = """                // SIMULASI VALVE AIR/GAS (Otomatis Menutup)
                myServo.write(90); // Putar 90 Derajat (Tutup Katup!)"""

content = content.replace(old_logic, new_logic)

# Replace standby comments to reflect Valve logic
content = content.replace("myServo.write(0); // Servo Standby", "myServo.write(0); // Valve Terbuka (Standby)")

with open('src/esp32_sensor_node/src/main.cpp', 'w') as f:
    f.write(content)

print("Servo Valve Logic Patched")
