import re

with open('src/esp32_sensor_node/src/OtaUpdater.cpp', 'r') as f:
    content = f.read()

target = """            Serial.println("[OTA] Anda sudah menggunakan versi terbaru atau sama.");
            }
        }
    } else {"""
replacement = """            Serial.println("[OTA] Anda sudah menggunakan versi terbaru atau sama.");
            }
        } else {
            ota_status = "ERROR_JSON_PARSE";
            Serial.print("[OTA] JSON Parse Failed: ");
            Serial.println(error.c_str());
        }
    } else {"""

content = content.replace(target, replacement)

with open('src/esp32_sensor_node/src/OtaUpdater.cpp', 'w') as f:
    f.write(content)
