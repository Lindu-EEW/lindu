with open('src/esp32_sensor_node/src/main.cpp', 'r') as f:
    cpp = f.read()

target_servo = '''                myServo.attach(SERVO_PIN, 500, 2400); // Sistem meng-enable motor

                if (is_valve_locked) {
                    myServo.write(90); // Sistem menggerakkan katup ke posisi Tutup (90)
                } else {
                    myServo.write(0);  // Sistem mereset katup ke posisi Buka (0)
                }

                vTaskDelay(pdMS_TO_TICKS(1000)); // Beri waktu 1 detik agar motor selesai berputar fisik
                myServo.detach(); // Sistem mematikan/melepas motor kembali (Hemat baterai & tidak memaksa)'''

replacement_servo = '''                // PRE-WRITE: Set target sudut SEBELUM motor dialiri listrik agar tidak melompat kaget
                int target_angle = is_valve_locked ? 90 : 0;
                myServo.write(target_angle); 
                
                // Beri jeda sangat kecil sebelum attach untuk stabilitas sinyal PWM FreeRTOS
                vTaskDelay(pdMS_TO_TICKS(50));
                
                // Nyalakan tenaga motor
                myServo.attach(SERVO_PIN, 500, 2400); 
                myServo.write(target_angle); // Tulis ulang untuk memastikan sinyal PWM terkirim

                // Beri waktu 2.5 detik (cukup panjang) agar motor yang membawa beban fisik berat
                // punya cukup waktu untuk sampai ke tujuan sebelum listriknya dicabut
                vTaskDelay(pdMS_TO_TICKS(2500)); 
                
                // Matikan aliran listrik (Zero-Torque Standby)
                myServo.detach();'''

cpp = cpp.replace(target_servo, replacement_servo)

with open('src/esp32_sensor_node/src/main.cpp', 'w') as f:
    f.write(cpp)

# Bump version
with open('src/esp32_sensor_node/src/OTAUpdater.h', 'r') as f:
    oh = f.read()
oh = oh.replace('#define CURRENT_VERSION "v1.2.4"', '#define CURRENT_VERSION "v1.2.5"')
with open('src/esp32_sensor_node/src/OTAUpdater.h', 'w') as f:
    f.write(oh)

