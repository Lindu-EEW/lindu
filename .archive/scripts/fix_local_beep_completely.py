import re

with open('src/esp32_sensor_node/src/main.cpp', 'r') as f:
    content = f.read()

def replacer(match):
    return """            } else if (is_local_alarm) {
                // DETEKSI GETARAN LOKAL (Menunggu Konfirmasi Node Lain): HANYA Berkedip Pink (Buzzer Hening)
                if ((millis() / 500) % 2 == 0) {
                    pixels.setPixelColor(0, pixels.Color(255, 20, 147)); // Hot Pink
                } else {
                    pixels.setPixelColor(0, pixels.Color(0, 0, 0));
                }
                digitalWrite(BUZZER_PIN, HIGH); // ACTIVE LOW: MATI"""

content = re.sub(r'            \} else if \(is_local_alarm\) \{.*?(?=\} else if \(!sensorMgr\.sensor_ok)', replacer, content, flags=re.DOTALL)

with open('src/esp32_sensor_node/src/main.cpp', 'w') as f:
    f.write(content)

