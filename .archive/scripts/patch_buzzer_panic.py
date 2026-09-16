import re

with open('src/esp32_sensor_node/src/main.cpp', 'r') as f:
    content = f.read()

target = '''                if ((millis() / 100) % 2 == 0) {
                    pixels.setPixelColor(0, pixels.Color(255, 0, 0));
                    analogWrite(BUZZER_PIN, 128); // 50% Duty Cycle (Max Volume Tone untuk Speaker)
                } else {
                    pixels.setPixelColor(0, pixels.Color(0, 0, 0));
                    pinMode(BUZZER_PIN, OUTPUT); digitalWrite(BUZZER_PIN, HIGH); // ACTIVE LOW: HIGH artinya MATI
                }'''

replacement = '''                if ((millis() / 100) % 2 == 0) {
                    pixels.setPixelColor(0, pixels.Color(255, 0, 0));
                    analogWrite(BUZZER_PIN, 128); // 50% Duty Cycle (Max Volume Tone untuk Speaker)
                } else {
                    pixels.setPixelColor(0, pixels.Color(0, 0, 0));
                    analogWrite(BUZZER_PIN, 255); // ACTIVE LOW: 100% Duty Cycle (HIGH) artinya MATI
                }'''

if "pinMode(BUZZER_PIN, OUTPUT);" in content:
    content = content.replace(target, replacement)
    
with open('src/esp32_sensor_node/src/main.cpp', 'w') as f:
    f.write(content)

