import re

with open('src/esp32_sensor_node/src/main.cpp', 'r') as f:
    main_content = f.read()

# Add local_alarm_until variable
if 'unsigned long local_alarm_until' not in main_content:
    main_content = main_content.replace('float local_latest_pga = 0.0;', 'float local_latest_pga = 0.0;\nunsigned long local_alarm_until = 0;')

# Update the queue pop logic to set the hold timer
old_queue = """        if (xQueueReceive(eventQueue, &ev, 0) == pdTRUE) {
            local_latest_pga = ev.pga;"""
new_queue = """        if (xQueueReceive(eventQueue, &ev, 0) == pdTRUE) {
            local_latest_pga = ev.pga;
            if (ev.pga > 0.05) local_alarm_until = millis() + 5000; // Tahan warna pink selama 5 detik"""
main_content = main_content.replace(old_queue, new_queue)

# Update LED Logic
old_led = """            bool is_global_alarm = (millis() < global_alarm_until && global_alarm_until > 0);
            bool is_local_alarm = (local_latest_pga > 0.05); // 0.05g threshold (light shaking)
            
            if (is_global_alarm || is_local_alarm) {
                // WARNING GEMPA! Berkedip Merah Terang & Cepat!
                if ((millis() / 100) % 2 == 0) pixels.setPixelColor(0, pixels.Color(255, 0, 0));
                else pixels.setPixelColor(0, pixels.Color(0, 0, 0));
            } else if (!sensorMgr.sensor_ok && !hw611_ok) {"""

new_led = """            bool is_global_alarm = (millis() < global_alarm_until && global_alarm_until > 0);
            bool is_local_alarm = (millis() < local_alarm_until && local_alarm_until > 0);
            
            if (is_global_alarm) {
                // KONFIRMASI GEMPA (DARI SERVER): Berkedip Merah Cepat (Strobo)
                if ((millis() / 100) % 2 == 0) pixels.setPixelColor(0, pixels.Color(255, 0, 0));
                else pixels.setPixelColor(0, pixels.Color(0, 0, 0));
            } else if (is_local_alarm) {
                // DETEKSI GETARAN LOKAL (Menunggu Konfirmasi Node Lain): Berkedip Pink Pelan
                if ((millis() / 500) % 2 == 0) pixels.setPixelColor(0, pixels.Color(255, 20, 147)); // Hot Pink
                else pixels.setPixelColor(0, pixels.Color(0, 0, 0));
            } else if (!sensorMgr.sensor_ok && !hw611_ok) {"""

main_content = main_content.replace(old_led, new_led)

with open('src/esp32_sensor_node/src/main.cpp', 'w') as f:
    f.write(main_content)

print("Pink LED Patched")
