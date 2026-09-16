import re

with open('src/esp32_sensor_node/src/SensorManager.cpp', 'r') as f:
    content = f.read()

old_logic = """    // SELALU KIRIM DATA SETIAP 1 DETIK
    if (millis() - _telemetry_last_send >= 1000) {
        SensorEvent ev = {pga, ratio, _current_hz, rms, dyn_x, dyn_y, dyn_z, millis(), temp, pres};
        xQueueSend(_eventQueue, &ev, 0);
        _telemetry_last_send = millis();
    }"""

new_logic = """    // LOGIKA PENGIRIMAN DATA (Zero-Delay saat Gempa)
    bool is_earthquake_spike = (pga > 0.05); // Threshold guncangan lokal
    
    // Kirim data BILA: Sedang gempa (minimal jeda 100ms agar queue tidak jebol) ATAU sudah 1 detik (kondisi normal)
    if ( (is_earthquake_spike && millis() - _telemetry_last_send >= 100) || (millis() - _telemetry_last_send >= 1000) ) {
        SensorEvent ev = {pga, ratio, _current_hz, rms, dyn_x, dyn_y, dyn_z, millis(), temp, pres};
        
        // Gunakan QueueSendToBack biasa, kecuali saat gempa kita gunakan QueueSendToFront agar diprioritaskan
        if (is_earthquake_spike) {
            xQueueSendToFront(_eventQueue, &ev, 0);
        } else {
            xQueueSend(_eventQueue, &ev, 0);
        }
        
        _telemetry_last_send = millis();
    }"""

content = content.replace(old_logic, new_logic)

with open('src/esp32_sensor_node/src/SensorManager.cpp', 'w') as f:
    f.write(content)

print("Zero-Delay Patched")
