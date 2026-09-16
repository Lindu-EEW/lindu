with open('src/esp32_sensor_node/src/NetworkManager.h', 'r') as f:
    h = f.read()

# Fix the literal \n
h = h.replace('\\n    void publishLog(const char* message);', '\n    void publishLog(const char* message);')

with open('src/esp32_sensor_node/src/NetworkManager.h', 'w') as f:
    f.write(h)
