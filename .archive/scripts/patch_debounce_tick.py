import re

with open('src/esp32_sensor_node/src/main.cpp', 'r') as f:
    content = f.read()

old_event = """            if (ev.pga > 0.12) {
                local_alarm_until = millis() + 5000; // Tahan warna pink selama 5 detik
                
                // TICK instan persis di detik terjadinya getaran fisik
                if (!is_global_alarm) { 
                    digitalWrite(BUZZER_PIN, LOW); // Active-Low ON
                    vTaskDelay(pdMS_TO_TICKS(15)); // Tahan 15ms
                    digitalWrite(BUZZER_PIN, HIGH); // Active-Low OFF
                }
            }"""

new_event = """            if (ev.pga > 0.12) {
                local_alarm_until = millis() + 5000; // Tahan warna pink selama 5 detik
                
                // TICK instan dengan Cooldown (Debounce) agar 1 ketukan = 1 bunyi
                static unsigned long last_tick_time = 0;
                if (!is_global_alarm && (millis() - last_tick_time > 500)) { 
                    last_tick_time = millis();
                    digitalWrite(BUZZER_PIN, LOW); // Active-Low ON
                    vTaskDelay(pdMS_TO_TICKS(20)); // Tahan 20ms agar terdengar jelas
                    digitalWrite(BUZZER_PIN, HIGH); // Active-Low OFF
                }
            }"""

content = content.replace(old_event, new_event)

with open('src/esp32_sensor_node/src/main.cpp', 'w') as f:
    f.write(content)

