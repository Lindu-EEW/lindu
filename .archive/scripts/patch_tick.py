import re

with open('src/esp32_sensor_node/src/main.cpp', 'r') as f:
    content = f.read()

old_local = """            } else if (is_local_alarm) {
                // DETEKSI GETARAN LOKAL (Menunggu Konfirmasi Node Lain): HANYA Berkedip Pink (Buzzer Hening)
                if ((millis() / 500) % 2 == 0) {
                    pixels.setPixelColor(0, pixels.Color(255, 20, 147)); // Hot Pink
                } else {
                    pixels.setPixelColor(0, pixels.Color(0, 0, 0));
                }
                digitalWrite(BUZZER_PIN, HIGH); // ACTIVE LOW: MATI"""

new_local = """            } else if (is_local_alarm) {
                // DETEKSI GETARAN LOKAL (Menunggu Konfirmasi Node Lain): Berkedip Pink + Suara TICK pelan
                if ((millis() / 500) % 2 == 0) {
                    pixels.setPixelColor(0, pixels.Color(255, 20, 147)); // Hot Pink
                    // Suara TICK super singkat (10ms) agar tidak nyaring
                    if (millis() % 500 < 10) digitalWrite(BUZZER_PIN, LOW); 
                    else digitalWrite(BUZZER_PIN, HIGH);
                } else {
                    pixels.setPixelColor(0, pixels.Color(0, 0, 0));
                    digitalWrite(BUZZER_PIN, HIGH);
                }"""

content = content.replace(old_local, new_local)

with open('src/esp32_sensor_node/src/main.cpp', 'w') as f:
    f.write(content)
