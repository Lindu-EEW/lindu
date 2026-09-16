import re

with open('src/esp32_sensor_node/src/main.cpp', 'r') as f:
    content = f.read()

old_event = """                // TICK instan dengan Cooldown (Debounce) agar 1 ketukan = 1 bunyi
                static unsigned long last_tick_time = 0;
                if (!is_global_alarm && (millis() - last_tick_time > 500)) { 
                    last_tick_time = millis();
                    digitalWrite(BUZZER_PIN, LOW); // Active-Low ON
                    vTaskDelay(pdMS_TO_TICKS(20)); // Tahan 20ms agar terdengar jelas
                    digitalWrite(BUZZER_PIN, HIGH); // Active-Low OFF
                }"""

new_event = """                // TICK Dinamis: Volume/Intensitas diwakili oleh durasi (Haptic Feedback)
                static unsigned long last_tick_time = 0;
                if (!is_global_alarm && (millis() - last_tick_time > 500)) { 
                    last_tick_time = millis();
                    
                    // Semakin besar getaran (PGA), semakin lama durasi beep-nya
                    int beep_duration = (int)(ev.pga * 40.0);
                    if (beep_duration < 5) beep_duration = 5;     // Getaran pelan = 5ms (Tik kecil)
                    if (beep_duration > 100) beep_duration = 100; // Getaran keras = 100ms (Bip panjang/keras)
                    
                    digitalWrite(BUZZER_PIN, LOW); // Active-Low ON
                    vTaskDelay(pdMS_TO_TICKS(beep_duration));
                    digitalWrite(BUZZER_PIN, HIGH); // Active-Low OFF
                }"""

content = content.replace(old_event, new_event)

with open('src/esp32_sensor_node/src/main.cpp', 'w') as f:
    f.write(content)

