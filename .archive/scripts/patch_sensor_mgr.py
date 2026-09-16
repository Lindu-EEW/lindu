with open("src/esp32_sensor_node/src/SensorManager.cpp", "r") as f:
    content = f.read()

old_logic = """    static unsigned long last_cuaca_check = 0;
    if (!bme_ok && !bmp_ok && millis() - last_cuaca_check > 5000) {
        bme_ok = _bme.begin(0x76, &Wire1) || _bme.begin(0x77, &Wire1);
        if (!bme_ok) bmp_ok = _bmp->begin(0x76) || _bmp->begin(0x77);
        last_cuaca_check = millis();
    }

    if (!sensor_ok && millis() - last_cuaca_check > 5000) {
        sensor_ok = selfTest();
    }"""

new_logic = """    static unsigned long last_cuaca_check = 0;
    if (!bme_ok && !bmp_ok && millis() - last_cuaca_check > 5000) {
        bme_ok = _bme.begin(0x76, &Wire1) || _bme.begin(0x77, &Wire1);
        if (!bme_ok) bmp_ok = _bmp->begin(0x76) || _bmp->begin(0x77);
        last_cuaca_check = millis();
    }

    static unsigned long last_accel_check = 0;
    if (!sensor_ok && millis() - last_accel_check > 5000) {
        sensor_ok = selfTest();
        if (sensor_ok) {
            _lsm6ds3.setAccelRange(LSM6DS_ACCEL_RANGE_8_G);
            _lsm6ds3.setAccelDataRate(LSM6DS_RATE_1_66K_HZ);
        }
        last_accel_check = millis();
    }"""

if old_logic in content:
    with open("src/esp32_sensor_node/src/SensorManager.cpp", "w") as f:
        f.write(content.replace(old_logic, new_logic))
    print("Success")
else:
    print("Not found")

