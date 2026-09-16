import re

with open('src/esp32_sensor_node/src/main.cpp', 'r') as f:
    content = f.read()

# 1. Remove tick from LED loop
old_local = """                // DETEKSI GETARAN LOKAL (Menunggu Konfirmasi Node Lain): Berkedip Pink + Suara TICK pelan
                if ((millis() / 500) % 2 == 0) {
                    pixels.setPixelColor(0, pixels.Color(255, 20, 147)); // Hot Pink
                    // Suara TICK super singkat (10ms) agar tidak nyaring
                    if (millis() % 500 < 10) digitalWrite(BUZZER_PIN, LOW); 
                    else digitalWrite(BUZZER_PIN, HIGH);
                } else {"""

new_local = """                // DETEKSI GETARAN LOKAL (Menunggu Konfirmasi Node Lain): HANYA Berkedip Pink
                if ((millis() / 500) % 2 == 0) {
                    pixels.setPixelColor(0, pixels.Color(255, 20, 147)); // Hot Pink
                } else {"""

content = content.replace(old_local, new_local)

# 2. Add real-time tick to the sensor event handler
old_event = """        // Cek apakah ada data sensor di antrean (Non-Blocking)
        if (xQueueReceive(eventQueue, &ev, 0) == pdTRUE) {
            local_latest_pga = ev.pga;
            if (ev.pga > 0.12) local_alarm_until = millis() + 5000; // Tahan warna pink selama 5 detik
            networkMgr.publishEvent("""

new_event = """        // Cek apakah ada data sensor di antrean (Non-Blocking)
        if (xQueueReceive(eventQueue, &ev, 0) == pdTRUE) {
            local_latest_pga = ev.pga;
            if (ev.pga > 0.12) {
                local_alarm_until = millis() + 5000; // Tahan warna pink selama 5 detik
                
                // TICK instan persis di detik terjadinya getaran fisik
                if (!is_global_alarm) { 
                    digitalWrite(BUZZER_PIN, LOW); // Active-Low ON
                    vTaskDelay(pdMS_TO_TICKS(15)); // Tahan 15ms
                    digitalWrite(BUZZER_PIN, HIGH); // Active-Low OFF
                }
            }
            networkMgr.publishEvent("""

content = content.replace(old_event, new_event)

with open('src/esp32_sensor_node/src/main.cpp', 'w') as f:
    f.write(content)

