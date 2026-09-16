import re

with open('src/esp32_sensor_node/src/main.cpp', 'r') as f:
    main_content = f.read()

# Add global variables
if 'unsigned long global_alarm_until' not in main_content:
    main_content = main_content.replace('QueueHandle_t eventQueue;', 'QueueHandle_t eventQueue;\nunsigned long global_alarm_until = 0;\nfloat local_latest_pga = 0.0;')

# Update local_latest_pga when ev is popped
old_queue = """        if (xQueueReceive(eventQueue, &ev, 0) == pdTRUE) {
            networkMgr.publishEvent("""
new_queue = """        if (xQueueReceive(eventQueue, &ev, 0) == pdTRUE) {
            local_latest_pga = ev.pga;
            networkMgr.publishEvent("""
main_content = main_content.replace(old_queue, new_queue)

# Update LED logic
old_led = """            bool hw611_ok = sensorMgr.bme_ok || sensorMgr.bmp_ok;
            
            if (!sensorMgr.sensor_ok && !hw611_ok) {"""
new_led = """            bool hw611_ok = sensorMgr.bme_ok || sensorMgr.bmp_ok;
            bool is_global_alarm = (millis() < global_alarm_until && global_alarm_until > 0);
            bool is_local_alarm = (local_latest_pga > 0.05); // 0.05g threshold (light shaking)
            
            if (is_global_alarm || is_local_alarm) {
                // WARNING GEMPA! Berkedip Merah Terang & Cepat!
                if ((millis() / 100) % 2 == 0) pixels.setPixelColor(0, pixels.Color(255, 0, 0));
                else pixels.setPixelColor(0, pixels.Color(0, 0, 0));
            } else if (!sensorMgr.sensor_ok && !hw611_ok) {"""
main_content = main_content.replace(old_led, new_led)

with open('src/esp32_sensor_node/src/main.cpp', 'w') as f:
    f.write(main_content)


with open('src/esp32_sensor_node/src/NetworkManager.cpp', 'r') as f:
    nm_content = f.read()

if 'extern unsigned long global_alarm_until;' not in nm_content:
    nm_content = nm_content.replace('#include "NetworkManager.h"', '#include "NetworkManager.h"\n\nextern unsigned long global_alarm_until;')

old_siren = """            if (dist < 50.0) {
                Serial.println("[!] SIRINE MENYALA! Epicenter berjarak < 50km.");
            }"""
new_siren = """            if (dist < 50.0) {
                Serial.println("[!] SIRINE MENYALA! Epicenter berjarak < 50km.");
                global_alarm_until = millis() + 30000; // Nyalakan alarm selama 30 detik
            }"""
nm_content = nm_content.replace(old_siren, new_siren)

with open('src/esp32_sensor_node/src/NetworkManager.cpp', 'w') as f:
    f.write(nm_content)

print("Warning LED Patched")
