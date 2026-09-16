import sys

with open('src/esp32_sensor_node/src/main.cpp', 'r') as f:
    content = f.read()

# 1. Define BOOT_BUTTON_PIN
if '#define BOOT_BUTTON_PIN 0' not in content:
    content = content.replace('ConfigManager configMgr;', '#define BOOT_BUTTON_PIN 0\n\nConfigManager configMgr;')

# 2. Add pinMode in setup()
if 'pinMode(BOOT_BUTTON_PIN, INPUT_PULLUP);' not in content:
    content = content.replace('Serial.begin(115200);', 'Serial.begin(115200);\n    pinMode(BOOT_BUTTON_PIN, INPUT_PULLUP);')

# 3. Add logic in loop()
logic = """
    // --- TOMBOL BOOT (FACTORY RESET) ---
    static unsigned long boot_press_time = 0;
    if (digitalRead(BOOT_BUTTON_PIN) == LOW) {
        if (boot_press_time == 0) {
            boot_press_time = millis();
        } else if (millis() - boot_press_time > 5000) { // Tahan 5 detik
            Serial.println("\\n[!] FACTORY RESET VIA TOMBOL BOOT DIMULAI!");
            digitalWrite(BUZZER_PIN, LOW); // Bunyikan bel
            configMgr.resetConfig();
            Preferences prefs;
            prefs.begin("ota", false); prefs.clear(); prefs.end();
            delay(1000);
            ESP.restart();
        }
    } else {
        boot_press_time = 0;
    }
"""
if 'TOMBOL BOOT' not in content:
    content = content.replace('void loop() {', 'void loop() {' + logic)

with open('src/esp32_sensor_node/src/main.cpp', 'w') as f:
    f.write(content)

