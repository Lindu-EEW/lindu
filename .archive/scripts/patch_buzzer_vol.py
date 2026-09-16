import re

with open('src/esp32_sensor_node/src/main.cpp', 'r') as f:
    content = f.read()

# Replace digitalWrite HIGH with analogWrite
content = content.replace("digitalWrite(BUZZER_PIN, HIGH);", "analogWrite(BUZZER_PIN, 5); // Volume sangat rendah (5 dari 255)")
content = content.replace("digitalWrite(BUZZER_PIN, LOW);", "analogWrite(BUZZER_PIN, 0);")

with open('src/esp32_sensor_node/src/main.cpp', 'w') as f:
    f.write(content)

print("Buzzer Volume Patched")
