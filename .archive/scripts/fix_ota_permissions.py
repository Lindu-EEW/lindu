import re

with open('src/esp32_sensor_node/.github/workflows/ota_release.yml', 'r') as f:
    content = f.read()

old_jobs = """jobs:
  build:"""

new_jobs = """permissions:
  contents: write

jobs:
  build:"""

if "permissions:" not in content:
    content = content.replace(old_jobs, new_jobs)

with open('src/esp32_sensor_node/.github/workflows/ota_release.yml', 'w') as f:
    f.write(content)
