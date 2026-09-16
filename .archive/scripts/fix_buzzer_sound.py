import re
with open('src/esp32_sensor_node/src/main.cpp', 'r') as f:
    content = f.read()

content = content.replace("analogWrite(BUZZER_PIN, 5); // Volume sangat rendah (5 dari 255)", "digitalWrite(BUZZER_PIN, HIGH); // Dikembalikan ke suara BEEP penuh agar jelas")
content = content.replace("analogWrite(BUZZER_PIN, 0);", "digitalWrite(BUZZER_PIN, LOW);")

with open('src/esp32_sensor_node/src/main.cpp', 'w') as f:
    f.write(content)
