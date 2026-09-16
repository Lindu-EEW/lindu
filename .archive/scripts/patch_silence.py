import re
with open('src/esp32_sensor_node/src/main.cpp', 'r') as f:
    content = f.read()

old_show = "        }\n        pixels.show();"
new_show = "        }\n        \n        // Matikan buzzer sepenuhnya jika kondisi aman\n        if (!is_global_alarm && !is_local_alarm) {\n            analogWrite(BUZZER_PIN, 0);\n        }\n        \n        pixels.show();"

content = content.replace(old_show, new_show)

with open('src/esp32_sensor_node/src/main.cpp', 'w') as f:
    f.write(content)
