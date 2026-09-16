import re

with open('src/esp32_sensor_node/src/SensorManager.cpp', 'r') as f:
    content = f.read()

# Just find the exact xQueueSend line
target = "if (millis() - _telemetry_last_send >= 1000) {"

if target in content:
    new_logic = """    // LOGIKA ZERO-DELAY
    bool is_earthquake_spike = (pga > 0.05); 
    
    if ( (is_earthquake_spike && millis() - _telemetry_last_send >= 100) || (millis() - _telemetry_last_send >= 1000) ) {"""
    content = content.replace(target, new_logic)
    
    # Also replace xQueueSend with conditional
    queue_target = "xQueueSend(_eventQueue, &ev, 0);"
    new_queue = """if (is_earthquake_spike) {
            xQueueSendToFront(_eventQueue, &ev, 0);
        } else {
            xQueueSend(_eventQueue, &ev, 0);
        }"""
    content = content.replace(queue_target, new_queue)
    
    with open('src/esp32_sensor_node/src/SensorManager.cpp', 'w') as f:
        f.write(content)
    print("Success")
else:
    print("Not found")

