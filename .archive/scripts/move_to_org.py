import os
import subprocess

# 1. Update Git Remotes
repos = {
    ".": "lindu",
    "src/esp32_sensor_node": "lindu_node",
    "src/server": "lindu_server",
    "src/dashboard-react": "lindu_react",
    "prototype/grafana-stack": "lindu_grafana"
}

for path, repo_name in repos.items():
    if os.path.exists(path):
        # Set remote to the new organization
        new_url = f"git@github.com:Lindu-EEW/{repo_name}.git"
        try:
            subprocess.run(["git", "-C", path, "remote", "set-url", "origin", new_url], check=True)
            print(f"Updated remote for {path} to {new_url}")
        except Exception as e:
            print(f"Failed to update {path}: {e}")

# 2. Update OTA Updater Code
ota_path = "src/esp32_sensor_node/src/OTAUpdater.h"
with open(ota_path, 'r') as f:
    code = f.read()

code = code.replace('#define REPO_OWNER "eatrisno"', '#define REPO_OWNER "Lindu-EEW"')
code = code.replace('#define CURRENT_VERSION "v1.1.15"', '#define CURRENT_VERSION "v1.1.16"')

with open(ota_path, 'w') as f:
    f.write(code)

print("Updated OTAUpdater.h to Lindu-EEW and bumped to v1.1.16")
