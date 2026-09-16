import re

with open('src/esp32_sensor_node/src/main.cpp', 'r') as f:
    content = f.read()

# Fix global alarm beep
old_global = """                // KONFIRMASI GEMPA (DARI SERVER): Berkedip Merah Cepat (Strobo) & Buzzer Menyala
                if ((millis() / 100) % 2 == 0) {
                    pixels.setPixelColor(0, pixels.Color(255, 0, 0));
                    digitalWrite(BUZZER_PIN, HIGH);
                } else {
                    pixels.setPixelColor(0, pixels.Color(0, 0, 0));
                    digitalWrite(BUZZER_PIN, LOW);
                }"""

new_global = """                // KONFIRMASI GEMPA (DARI SERVER): Berkedip Merah Cepat (Strobo) & Buzzer Menyala (Keras)
                if ((millis() / 100) % 2 == 0) {
                    pixels.setPixelColor(0, pixels.Color(255, 0, 0));
                    analogWrite(BUZZER_PIN, 128); // 50% Duty Cycle (Max Volume Tone)
                } else {
                    pixels.setPixelColor(0, pixels.Color(0, 0, 0));
                    analogWrite(BUZZER_PIN, 0);
                }"""
content = content.replace(old_global, new_global)

# Add local alarm low level beep
old_local = """            } else if (is_local_alarm) {
                // DETEKSI GETARAN LOKAL (Menunggu Konfirmasi Node Lain): Berkedip Pink Pelan
                if ((millis() / 500) % 2 == 0) pixels.setPixelColor(0, pixels.Color(255, 20, 147)); // Hot Pink
                else pixels.setPixelColor(0, pixels.Color(0, 0, 0));
                
                myServo.write(0);  // Normal (Buka)
            }
            
            // Matikan buzzer jika bukan global alarm
            if (!is_global_alarm) digitalWrite(BUZZER_PIN, LOW);"""

new_local = """            } else if (is_local_alarm) {
                // DETEKSI GETARAN LOKAL (Menunggu Konfirmasi): Berkedip Pink & Low Level Beep
                if ((millis() / 500) % 2 == 0) {
                    pixels.setPixelColor(0, pixels.Color(255, 20, 147)); // Hot Pink
                    analogWrite(BUZZER_PIN, 2); // Duty Cycle sangat kecil (Low Volume Tone)
                } else {
                    pixels.setPixelColor(0, pixels.Color(0, 0, 0));
                    analogWrite(BUZZER_PIN, 0);
                }
                
                myServo.write(0);  // Normal (Buka)
            }
            
            // Matikan buzzer jika aman (Bukan global & Bukan local alarm)
            if (!is_global_alarm && !is_local_alarm) analogWrite(BUZZER_PIN, 0);"""
content = content.replace(old_local, new_local)

# Fix setup pin initialization to prevent analogWrite conflict
content = content.replace("digitalWrite(BUZZER_PIN, LOW);", "analogWrite(BUZZER_PIN, 0);")

with open('src/esp32_sensor_node/src/main.cpp', 'w') as f:
    f.write(content)

print("Low Level Beep Patched")
