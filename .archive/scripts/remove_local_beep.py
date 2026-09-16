import re
with open('src/esp32_sensor_node/src/main.cpp', 'r') as f:
    content = f.read()

old_local = """                // DETEKSI GETARAN LOKAL (Menunggu Konfirmasi): Berkedip Pink & Nada Pelan (Tick singkat)
                if ((millis() / 500) % 2 == 0) {
                    pixels.setPixelColor(0, pixels.Color(255, 20, 147)); // Hot Pink
                    if (millis() % 500 < 50) digitalWrite(BUZZER_PIN, LOW); // Nyala sangat singkat (Tick)
                    else digitalWrite(BUZZER_PIN, HIGH);
                } else {
                    pixels.setPixelColor(0, pixels.Color(0, 0, 0));
                    digitalWrite(BUZZER_PIN, HIGH);
                }"""

new_local = """                // DETEKSI GETARAN LOKAL (Menunggu Konfirmasi): HANYA Berkedip Pink (Buzzer Hening)
                if ((millis() / 500) % 2 == 0) {
                    pixels.setPixelColor(0, pixels.Color(255, 20, 147)); // Hot Pink
                } else {
                    pixels.setPixelColor(0, pixels.Color(0, 0, 0));
                }
                digitalWrite(BUZZER_PIN, HIGH); // Buzzer tetap MATI selama fase menunggu"""

content = content.replace(old_local, new_local)

with open('src/esp32_sensor_node/src/main.cpp', 'w') as f:
    f.write(content)
