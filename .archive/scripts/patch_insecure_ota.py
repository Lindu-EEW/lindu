import re

with open('src/esp32_sensor_node/src/OtaUpdater.cpp', 'r') as f:
    content = f.read()

# Replace setCACert with setInsecure for the API call
old_client = """    WiFiClientSecure client;
    client.setCACert(rootCACertificate);"""

new_client = """    WiFiClientSecure client;
    client.setInsecure(); // Bypass CA validation since GitHub rotates certificates"""

content = content.replace(old_client, new_client)

# Fix httpUpdate to also be insecure
# But wait, httpsUpdate uses ESPhttpUpdate.update(client, bin_url) or HTTPClient?
# In the code, it uses ESPhttpUpdate.update(bin_url) ? No, let's look at how it downloads.
