import re

with open('src/esp32_sensor_node/src/main.cpp', 'r') as f:
    content = f.read()

# Fix setup to ensure it starts OFF (HIGH)
old_setup = "noTone(BUZZER_PIN); pinMode(BUZZER_PIN, INPUT);"
new_setup = "pinMode(BUZZER_PIN, OUTPUT); digitalWrite(BUZZER_PIN, HIGH); // ACTIVE LOW: HIGH artinya MATI"
content = content.replace(old_setup, new_setup)

# Fix Global Alarm (Loud Beep)
old_global = """                // KONFIRMASI GEMPA (DARI SERVER): Berkedip Merah Cepat (Strobo) & Bunyikan Speaker
                if ((millis() / 100) % 2 == 0) {
                    pixels.setPixelColor(0, pixels.Color(255, 0, 0));
                    tone(BUZZER_PIN, 2000); // Nada tinggi melengking
                } else {
                    pixels.setPixelColor(0, pixels.Color(0, 0, 0));
                    noTone(BUZZER_PIN);
                }"""

new_global = """                // KONFIRMASI GEMPA (DARI SERVER): Berkedip Merah Cepat (Strobo) & Bunyikan Speaker
                if ((millis() / 100) % 2 == 0) {
                    pixels.setPixelColor(0, pixels.Color(255, 0, 0));
                    digitalWrite(BUZZER_PIN, LOW); // ACTIVE LOW: LOW = MENYALA KERAS
                } else {
                    pixels.setPixelColor(0, pixels.Color(0, 0, 0));
                    digitalWrite(BUZZER_PIN, HIGH); // ACTIVE LOW: HIGH = MATI
                }"""
content = content.replace(old_global, new_global)

# Fix Local Alarm (Soft Tick/Beep)
old_local = """                // DETEKSI GETARAN LOKAL (Menunggu Konfirmasi): Berkedip Pink & Nada Pelan
                if ((millis() / 500) % 2 == 0) {
                    pixels.setPixelColor(0, pixels.Color(255, 20, 147)); // Hot Pink
                    tone(BUZZER_PIN, 500); // Nada rendah (Low level bass)
                } else {
                    pixels.setPixelColor(0, pixels.Color(0, 0, 0));
                    noTone(BUZZER_PIN);
                }"""

new_local = """                // DETEKSI GETARAN LOKAL (Menunggu Konfirmasi): Berkedip Pink & Nada Pelan (Tick singkat)
                if ((millis() / 500) % 2 == 0) {
                    pixels.setPixelColor(0, pixels.Color(255, 20, 147)); // Hot Pink
                    if (millis() % 500 < 50) digitalWrite(BUZZER_PIN, LOW); // Nyala sangat singkat (Tick)
                    else digitalWrite(BUZZER_PIN, HIGH);
                } else {
                    pixels.setPixelColor(0, pixels.Color(0, 0, 0));
                    digitalWrite(BUZZER_PIN, HIGH);
                }"""
content = content.replace(old_local, new_local)

# Fix Silence State Tracker
old_tracker = """        // Matikan speaker sepenuhnya jika kondisi aman
        static bool is_buzzer_active = false;
        
        if (is_global_alarm || is_local_alarm) {
            is_buzzer_active = true;
        } else {
            if (is_buzzer_active) {
                noTone(BUZZER_PIN); // Matikan nada
                pinMode(BUZZER_PIN, INPUT); // Paksa pin menjadi netral (High-Impedance) untuk memutus arus ke speaker
                is_buzzer_active = false;
            }
        }"""

new_tracker = """        // Matikan speaker sepenuhnya jika kondisi aman
        static bool is_buzzer_active = false;
        
        if (is_global_alarm || is_local_alarm) {
            is_buzzer_active = true;
        } else {
            if (is_buzzer_active) {
                pinMode(BUZZER_PIN, OUTPUT);
                digitalWrite(BUZZER_PIN, HIGH); // ACTIVE LOW: HIGH mematikan arus sepenuhnya
                is_buzzer_active = false;
            }
        }"""
content = content.replace(old_tracker, new_tracker)

with open('src/esp32_sensor_node/src/main.cpp', 'w') as f:
    f.write(content)

print("Active Low Patched")
