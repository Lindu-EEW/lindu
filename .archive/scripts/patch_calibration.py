import re

with open('src/esp32_sensor_node/src/SensorManager.cpp', 'r') as f:
    content = f.read()

old_logic = """    float alpha_dc = _is_calibrated ? 0.002 : 0.1;
    _dc_x = (accel.acceleration.x * alpha_dc) + (_dc_x * (1.0 - alpha_dc));
    _dc_y = (accel.acceleration.y * alpha_dc) + (_dc_y * (1.0 - alpha_dc));
    _dc_z = (accel.acceleration.z * alpha_dc) + (_dc_z * (1.0 - alpha_dc));

    static unsigned long init_time = millis();
    if (millis() - init_time > 2000)
      _is_calibrated = true;"""

new_logic = """    static bool is_first_read = true;
    if (is_first_read) {
      _dc_x = accel.acceleration.x;
      _dc_y = accel.acceleration.y;
      _dc_z = accel.acceleration.z;
      is_first_read = false;
      _is_calibrated = true;
    }

    float alpha_dc = 0.002;
    _dc_x = (accel.acceleration.x * alpha_dc) + (_dc_x * (1.0 - alpha_dc));
    _dc_y = (accel.acceleration.y * alpha_dc) + (_dc_y * (1.0 - alpha_dc));
    _dc_z = (accel.acceleration.z * alpha_dc) + (_dc_z * (1.0 - alpha_dc));"""

content = content.replace(old_logic, new_logic)

with open('src/esp32_sensor_node/src/SensorManager.cpp', 'w') as f:
    f.write(content)

print("Calibration Patched")
