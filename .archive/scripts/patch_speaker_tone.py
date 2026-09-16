import re

with open('src/esp32_sensor_node/src/main.cpp', 'r') as f:
    content = f.read()

# Replace Global Alarm analogWrite with tone()
old_global = """                // KONFIRMASI GEMPA (DARI SERVER): Berkedip Merah Cepat (Strobo) & Buzzer Menyala (Keras)
                if ((millis() / 100) % 2 == 0) {
                    pixels.setPixelColor(0, pixels.Color(255, 0, 0));
                    analogWrite(BUZZER_PIN, 128); // 50% Duty Cycle (Max Volume Tone untuk Speaker)
                } else {
                    pixels.setPixelColor(0, pixels.Color(0, 0, 0));
                    analogWrite(BUZZER_PIN, 0);
                }"""

new_global = """                // KONFIRMASI GEMPA (DARI SERVER): Berkedip Merah Cepat (Strobo) & Bunyikan Speaker
                if ((millis() / 100) % 2 == 0) {
                    pixels.setPixelColor(0, pixels.Color(255, 0, 0));
                    tone(BUZZER_PIN, 2000); // Nada tinggi melengking
                } else {
                    pixels.setPixelColor(0, pixels.Color(0, 0, 0));
                    noTone(BUZZER_PIN);
                }"""
content = content.replace(old_global, new_global)

# Replace Local Alarm analogWrite with tone()
old_local = """                // DETEKSI GETARAN LOKAL (Menunggu Konfirmasi): Berkedip Pink & Low Level Beep
                if ((millis() / 500) % 2 == 0) {
                    pixels.setPixelColor(0, pixels.Color(255, 20, 147)); // Hot Pink
                    analogWrite(BUZZER_PIN, 2); // 1% Duty Cycle (Sangat pelan untuk Speaker)
                } else {
                    pixels.setPixelColor(0, pixels.Color(0, 0, 0));
                    analogWrite(BUZZER_PIN, 0);
                }"""

new_local = """                // DETEKSI GETARAN LOKAL (Menunggu Konfirmasi): Berkedip Pink & Nada Pelan
                if ((millis() / 500) % 2 == 0) {
                    pixels.setPixelColor(0, pixels.Color(255, 20, 147)); // Hot Pink
                    tone(BUZZER_PIN, 500); // Nada rendah (Low level bass)
                } else {
                    pixels.setPixelColor(0, pixels.Color(0, 0, 0));
                    noTone(BUZZER_PIN);
                }"""
content = content.replace(old_local, new_local)

# Replace the state tracker silence logic with noTone() and INPUT mode
old_tracker = """        // Matikan buzzer sepenuhnya jika kondisi aman (Gunakan State Tracker untuk mencegah glitch PWM)
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

new_tracker = """        // Matikan speaker sepenuhnya jika kondisi aman
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
content = content.replace(old_tracker, new_tracker)

# Also fix the initial setup to ensure noTone
content = content.replace("analogWrite(BUZZER_PIN, 0);", "noTone(BUZZER_PIN); pinMode(BUZZER_PIN, INPUT);")

with open('src/esp32_sensor_node/src/main.cpp', 'w') as f:
    f.write(content)

print("Tone Logic Patched")
