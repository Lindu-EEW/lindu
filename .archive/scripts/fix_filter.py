import re

with open('src/esp32_sensor_node/src/OtaUpdater.cpp', 'r') as f:
    content = f.read()

target = '''        StaticJsonDocument<200> filter;
        filter["tag_name"] = true;'''
replacement = '''        StaticJsonDocument<200> filter;
        filter["tag_name"] = true;
        filter["assets"][0]["name"] = true;
        filter["assets"][0]["browser_download_url"] = true;'''

content = content.replace(target, replacement)

# Add else handler for missing bin
target2 = '''                        ota_status = "ERROR_UPDATE_FAILED";
                        Serial.println("[OTA] Update gagal!");
                    }
                }
            } else {'''
replacement2 = '''                        ota_status = "ERROR_UPDATE_FAILED";
                        Serial.println("[OTA] Update gagal!");
                    }
                } else {
                    ota_status = "ERROR_NO_BIN_FOUND"; networkMgr.forcePublishStatus();
                    Serial.println("[OTA] Gagal: Tidak ada file .bin di GitHub Release ini!");
                }
            } else {'''

content = content.replace(target2, replacement2)

with open('src/esp32_sensor_node/src/OtaUpdater.cpp', 'w') as f:
    f.write(content)
