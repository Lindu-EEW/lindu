import re

with open('src/esp32_sensor_node/src/OtaUpdater.cpp', 'r') as f:
    content = f.read()

# Add extern pixels at the top
old_include = '#include "esp_system.h"\n'
new_include = '#include "esp_system.h"\n#include <Adafruit_NeoPixel.h>\nextern Adafruit_NeoPixel pixels;\n'
if "extern Adafruit_NeoPixel pixels;" not in content:
    content = content.replace('#include "esp_system.h"\n', new_include)
elif '#include "esp_system.h"' not in content:
    content = '#include <Adafruit_NeoPixel.h>\nextern Adafruit_NeoPixel pixels;\n' + content

# Add onProgress callback
old_begin = """    bool canBegin = Update.begin(contentLength, U_FLASH);
    
    if (canBegin) {
        Serial.println("[OTA] Memulai penulisan ke memori Flash...");
        size_t written = Update.writeStream(http.getStream());"""

new_begin = """    bool canBegin = Update.begin(contentLength, U_FLASH);
    
    if (canBegin) {
        Serial.println("[OTA] Memulai penulisan ke memori Flash...");
        
        Update.onProgress([](size_t progress, size_t total) {
            static unsigned long last_blink = 0;
            if (millis() - last_blink > 100) { // Berkedip Cyan cepat tiap 100ms
                last_blink = millis();
                static bool toggle = false;
                toggle = !toggle;
                pixels.setPixelColor(0, toggle ? pixels.Color(0, 255, 255) : pixels.Color(0, 0, 0)); // Cyan = Updating
                pixels.show();
            }
            if (progress % (total / 10) == 0) {
                Serial.printf("[OTA] Progress: %u%%\\n", (progress / (total / 100)));
            }
        });
        
        size_t written = Update.writeStream(http.getStream());"""

content = content.replace(old_begin, new_begin)

with open('src/esp32_sensor_node/src/OtaUpdater.cpp', 'w') as f:
    f.write(content)
