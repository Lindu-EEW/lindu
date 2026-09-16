import re
with open('src/esp32_sensor_node/src/main.cpp', 'r') as f:
    content = f.read()

# Add #include <ESP32Servo.h> and global servo var
if "<ESP32Servo.h>" not in content:
    content = content.replace("#include <WiFi.h>", "#include <WiFi.h>\n#include <ESP32Servo.h>")
    content = content.replace("#define RGB_PIN 48", "#define RGB_PIN 48\n#define SERVO_PIN 5\n\nServo myServo;")

# Initialize servo in networkTaskCode
old_init = "pixels.begin();"
new_init = "pixels.begin();\n    myServo.setPeriodHertz(50);\n    myServo.attach(SERVO_PIN);\n    myServo.write(0);"
content = content.replace(old_init, new_init)

# Add servo sweep inside while(1) loop
old_sweep = "if (is_global_alarm) {\n                // KONFIRMASI GEMPA (DARI SERVER): Berkedip Merah Cepat (Strobo)"
new_sweep = """if (is_global_alarm) {
                // Ayunkan Servo Kiri-Kanan
                int servo_angle = (millis() / 200) % 2 == 0 ? 90 : 0;
                myServo.write(servo_angle);
                
                // KONFIRMASI GEMPA (DARI SERVER): Berkedip Merah Cepat (Strobo)"""
content = content.replace(old_sweep, new_sweep)

# Add servo standby to local_alarm or normal state
old_standby = "else if (is_local_alarm) {"
new_standby = """else if (is_local_alarm) {
                myServo.write(0); // Servo Standby"""
content = content.replace(old_standby, new_standby)

old_standby2 = "else if (!sensorMgr.sensor_ok && !hw611_ok) {"
new_standby2 = """else if (!sensorMgr.sensor_ok && !hw611_ok) {
                myServo.write(0); // Servo Standby"""
content = content.replace(old_standby2, new_standby2)

with open('src/esp32_sensor_node/src/main.cpp', 'w') as f:
    f.write(content)
print("Servo logic injected into main.cpp")
