import re

with open('src/esp32_sensor_node/src/main.cpp', 'r') as f:
    content = f.read()

# Remove auto-enable from setup
old_init = """    // ESP32-S3 PWM Timer Allocation untuk Servo
    ESP32PWM::allocateTimer(0);
    ESP32PWM::allocateTimer(1);
    ESP32PWM::allocateTimer(2);
    ESP32PWM::allocateTimer(3);
    myServo.setPeriodHertz(50);
    myServo.attach(SERVO_PIN, 500, 2400); // Lebar pulsa standar Servo SG90
    myServo.write(0);"""

new_init = """    // ESP32-S3 PWM Timer Allocation untuk Servo (Hanya alokasi, tidak di-enable)
    ESP32PWM::allocateTimer(0);
    ESP32PWM::allocateTimer(1);
    ESP32PWM::allocateTimer(2);
    ESP32PWM::allocateTimer(3);
    myServo.setPeriodHertz(50);
    // Servo sengaja TIDAK di-attach di sini agar tidak auto-enable saat alat menyala"""

content = content.replace(old_init, new_init)

# Add attach and detach to the state logic
old_logic = """            // LOGIKA VALVE MANUAL RESET (EDGE TRIGGER agar Servo tidak bergetar/buzzer)
            static bool last_valve_state = false;
            if (is_valve_locked != last_valve_state) {
                if (is_valve_locked) {
                    myServo.write(90); // Mengunci (Tutup) sampai direset
                } else {
                    myServo.write(0);  // Normal (Buka)
                }
                last_valve_state = is_valve_locked;
            }"""

new_logic = """            // LOGIKA VALVE MANUAL RESET (Hanya nyalakan motor saat diperintah sistem)
            static bool last_valve_state = false;
            if (is_valve_locked != last_valve_state) {
                myServo.attach(SERVO_PIN, 500, 2400); // Sistem meng-enable motor
                
                if (is_valve_locked) {
                    myServo.write(90); // Sistem menggerakkan katup ke posisi Tutup (90)
                } else {
                    myServo.write(0);  // Sistem mereset katup ke posisi Buka (0)
                }
                
                vTaskDelay(pdMS_TO_TICKS(1000)); // Beri waktu 1 detik agar motor selesai berputar fisik
                myServo.detach(); // Sistem mematikan/melepas motor kembali (Hemat baterai & tidak memaksa)
                
                last_valve_state = is_valve_locked;
            }"""

content = content.replace(old_logic, new_logic)

with open('src/esp32_sensor_node/src/main.cpp', 'w') as f:
    f.write(content)

print("Servo Detach Logic Patched")
