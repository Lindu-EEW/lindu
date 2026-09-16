import re

with open('src/esp32_sensor_node/src/main.cpp', 'r') as f:
    content = f.read()

# Completely rewrite the alarm section
def replacer(match):
    return """            if (is_global_alarm) {
                // KONFIRMASI GEMPA (DARI SERVER): Berkedip Merah Cepat (Strobo) & Buzzer Menyala
                if ((millis() / 100) % 2 == 0) {
                    pixels.setPixelColor(0, pixels.Color(255, 0, 0));
                    analogWrite(BUZZER_PIN, 128); // 50% Duty Cycle (Max Volume Tone untuk Speaker)
                } else {
                    pixels.setPixelColor(0, pixels.Color(0, 0, 0));
                    analogWrite(BUZZER_PIN, 0);
                }
            } else if (is_local_alarm) {
                // DETEKSI GETARAN LOKAL (Menunggu Konfirmasi Node Lain): Berkedip Pink & Low Level Beep
                if ((millis() / 500) % 2 == 0) {
                    pixels.setPixelColor(0, pixels.Color(255, 20, 147)); // Hot Pink
                    analogWrite(BUZZER_PIN, 2); // 1% Duty Cycle (Sangat pelan untuk Speaker)
                } else {
                    pixels.setPixelColor(0, pixels.Color(0, 0, 0));
                    analogWrite(BUZZER_PIN, 0);
                }
            } else if (!sensorMgr.sensor_ok && !hw611_ok) {"""

content = re.sub(r'            if \(is_global_alarm\) \{.*?\} else if \(!sensorMgr.sensor_ok && !hw611_ok\) \{', replacer, content, flags=re.DOTALL)

content = re.sub(r'// Matikan buzzer jika bukan global alarm\s*if \(!is_global_alarm\) digitalWrite\(BUZZER_PIN, LOW\);', '// Matikan buzzer jika aman (Bukan global & local alarm)\n            if (!is_global_alarm && !is_local_alarm) analogWrite(BUZZER_PIN, 0);', content)
content = re.sub(r'digitalWrite\(BUZZER_PIN, LOW\);', 'analogWrite(BUZZER_PIN, 0);', content)

with open('src/esp32_sensor_node/src/main.cpp', 'w') as f:
    f.write(content)
