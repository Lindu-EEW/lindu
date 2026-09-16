import re

with open('src/esp32_sensor_node/src/OTAUpdater.cpp', 'r') as f:
    content = f.read()

target = '''    String url = String("https://api.github.com/repos/") + REPO_OWNER + "/" + REPO_NAME + "/releases/latest";
    http.begin(client, url);
    int httpCode = http.GET();'''

replace = '''    String url = String("https://api.github.com/repos/") + REPO_OWNER + "/" + REPO_NAME + "/releases/latest";
    http.setFollowRedirects(HTTPC_STRICT_FOLLOW_REDIRECTS); // Wajib agar bisa mengikuti redirect jika Repo pindah organisasi
    http.begin(client, url);
    int httpCode = http.GET();'''

if "setFollowRedirects" not in target:
    content = content.replace(target, replace)

with open('src/esp32_sensor_node/src/OTAUpdater.cpp', 'w') as f:
    f.write(content)
