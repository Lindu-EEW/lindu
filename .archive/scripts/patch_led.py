with open("src/esp32_sensor_node/src/main.cpp", "r") as f:
    content = f.read()

old_led_code = """        // Animasi LED "Bernafas" Halus (Breathing LED)
        if (WiFi.status() == WL_CONNECTED) {
            breathAngle += 0.05;
            if (breathAngle > 2 * PI) breathAngle -= 2 * PI;
            // Gelombang sinus dari 0 sampai 40 (cahaya sangat lembut)
            int brightness = (sin(breathAngle) + 1.0) * 20.0; 
            pixels.setPixelColor(0, pixels.Color(0, brightness, 0)); // Hijau Lembut
            pixels.show();
        } else {
            // Berkedip merah pelan jika Wi-Fi putus
            if ((millis() / 500) % 2 == 0) {
                pixels.setPixelColor(0, pixels.Color(30, 0, 0));
            } else {
                pixels.setPixelColor(0, pixels.Color(0, 0, 0));
            }
            pixels.show();
        }"""

new_led_code = """        // Animasi LED Cerdas (Sesuai Status Sensor & WiFi)
        if (WiFi.status() == WL_CONNECTED) {
            breathAngle += 0.05;
            if (breathAngle > 2 * PI) breathAngle -= 2 * PI;
            int brightness = (sin(breathAngle) + 1.0) * 20.0; 
            
            bool hw611_ok = sensorMgr.bme_ok || sensorMgr.bmp_ok;
            
            if (!sensorMgr.sensor_ok && !hw611_ok) {
                // Semua sensor mati: Berkedip Merah Cepat (Bahaya Fatal)
                if ((millis() / 200) % 2 == 0) pixels.setPixelColor(0, pixels.Color(50, 0, 0));
                else pixels.setPixelColor(0, pixels.Color(0, 0, 0));
            } else if (!sensorMgr.sensor_ok) {
                // Akselerometer mati: Bernafas Merah
                pixels.setPixelColor(0, pixels.Color(brightness, 0, 0));
            } else if (!hw611_ok) {
                // Suhu mati: Bernafas Kuning/Oranye
                pixels.setPixelColor(0, pixels.Color(brightness, brightness * 0.5, 0));
            } else {
                // Semua normal: Bernafas Hijau
                pixels.setPixelColor(0, pixels.Color(0, brightness, 0));
            }
        } else {
            // Berkedip Merah Pelan jika Wi-Fi putus
            if ((millis() / 500) % 2 == 0) pixels.setPixelColor(0, pixels.Color(30, 0, 0));
            else pixels.setPixelColor(0, pixels.Color(0, 0, 0));
        }
        pixels.show();"""

if old_led_code in content:
    with open("src/esp32_sensor_node/src/main.cpp", "w") as f:
        f.write(content.replace(old_led_code, new_led_code))
    print("Success")
else:
    print("Code not found")
