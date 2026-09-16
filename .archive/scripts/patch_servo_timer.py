import re
with open('src/esp32_sensor_node/src/main.cpp', 'r') as f:
    content = f.read()

old_init = """    pixels.begin();
    myServo.setPeriodHertz(50);
    myServo.attach(SERVO_PIN);
    myServo.write(0);"""

new_init = """    pixels.begin();
    
    // ESP32-S3 PWM Timer Allocation untuk Servo
    ESP32PWM::allocateTimer(0);
    ESP32PWM::allocateTimer(1);
    ESP32PWM::allocateTimer(2);
    ESP32PWM::allocateTimer(3);
    myServo.setPeriodHertz(50);
    myServo.attach(SERVO_PIN, 500, 2400); // Lebar pulsa standar Servo SG90
    myServo.write(0);"""

content = content.replace(old_init, new_init)

with open('src/esp32_sensor_node/src/main.cpp', 'w') as f:
    f.write(content)
