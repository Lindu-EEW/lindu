with open('src/esp32_sensor_node/src/main.cpp', 'r') as f:
    cpp = f.read()

# Cari blok dimana local_alarm_until diset
target = '''            if (ev.pga > 0.12) {
                local_alarm_until = millis() + 5000; // Tahan warna pink selama 5 detik'''

replacement = '''            if (ev.pga > 0.12) {
                local_alarm_until = millis() + 5000; // Tahan warna pink selama 5 detik
                
                // ========== OFFLINE FAIL-SAFE (LONE WOLF MODE) ==========
                // Jika MQTT server mati DAN getaran AMAT SANGAT BRUTAL (PGA > 0.60G),
                // ESP32 mengambil alih kekuasaan mutlak: langsung membunyikan sirine,
                // mengunci katup gas, dan membuka pintu untuk evakuasi.
                // Ini adalah garis pertahanan terakhir saat infrastruktur internet runtuh.
                if (!networkMgr.isConnected() && ev.pga > 0.60) {
                    Serial.println("[!!!] LONE WOLF MODE: Server offline + PGA EKSTREM! Mengambil alih kendali!");
                    global_alarm_until = millis() + 15000; // Sirine merah 15 detik
                    is_valve_locked = true;
                    actPrefs.putBool("valve_locked", true);
#if !ARDUINO_USB_CDC_ON_BOOT
                    is_door_locked = false; // Buka pintu untuk evakuasi (Classic only)
#endif
                }'''

cpp = cpp.replace(target, replacement)

# Bump version
cpp2 = open('src/esp32_sensor_node/src/OTAUpdater.h', 'r').read()
cpp2 = cpp2.replace('#define CURRENT_VERSION "v1.2.0"', '#define CURRENT_VERSION "v1.2.1"')
open('src/esp32_sensor_node/src/OTAUpdater.h', 'w').write(cpp2)

with open('src/esp32_sensor_node/src/main.cpp', 'w') as f:
    f.write(cpp)
