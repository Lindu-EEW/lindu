import re

with open('src/esp32_sensor_node/src/OTAUpdater.cpp', 'r') as f:
    content = f.read()

# Hapus penggunaan NeoPixel (pixels.show) dari dalam callback Update.onProgress
# karena mematikan interrupt saat flash memori sedang ditulis akan menyebabkan hard-freeze.
target = '''        Update.onProgress([](size_t progress, size_t total) {
            static unsigned long last_blink = 0;
            if (millis() - last_blink > 100) { // Berkedip Cyan cepat tiap 100ms
                last_blink = millis();
                static bool toggle = false;
                toggle = !toggle;
                pixels.setPixelColor(0, toggle ? pixels.Color(255, 255, 0) : pixels.Color(0, 0, 0)); // Yellow = Updating
                pixels.show();
            }
            if (progress % (total / 10) == 0) {
                Serial.printf("[OTA] Progress: %u%%\\n", (progress / (total / 100)));
            }
        });'''

replace = '''        Update.onProgress([](size_t progress, size_t total) {
            if (progress % (total / 10) == 0) {
                Serial.printf("[OTA] Progress: %u%%\\n", (progress / (total / 100)));
            }
        });'''

content = content.replace(target, replace)

with open('src/esp32_sensor_node/src/OTAUpdater.cpp', 'w') as f:
    f.write(content)
