with open('docs/05_DEPLOYMENT_PLAN.md', 'r') as f:
    lines = f.readlines()

new_content = """
### 4. CI/CD Cloud OTA Release (GitHub Actions)

Lindu.id utilizes an automated CI/CD pipeline (`.github/workflows/ota_release.yml`) for seamless over-the-air firmware deployments. The system uses an **Auto-Versioning** strategy tied to GitHub Run Numbers.

**How the New Flow Works:**
1. **Push to Main:** A developer pushes or merges new C++ code into the `main` branch.
2. **Automated Matrix Build:** GitHub Actions automatically wakes up and compiles the firmware concurrently for multiple hardware variants (e.g., `esp32s3` and `esp32_wroom`).
3. **Auto-Increment Versioning:** The pipeline automatically intercepts the C++ source code during compilation and injects the `$GITHUB_RUN_NUMBER` into `src/OTAUpdater.h`. For example, if this is the 67th build, the firmware is hardcoded as `v1.4.67`. This entirely eliminates the need for developers to manually run `git tag`.
4. **Automated GitHub Release:** Once compiled, the `.bin` files are uploaded and attached to a new GitHub Release labeled `Auto Release v1.4.67`.
5. **Remote Command (Grafana):** The dashboard administrator clicks **[FORCE OTA UPDATE]** in the Command Center. The Python Server broadcasts the update command over MQTT (`lindu/sensor/cmd/all`), and all physical ESP32 nodes pull the newly compiled `.bin` over HTTPS and restart themselves.

> [!TIP]
> **No Manual Tagging Required!** You no longer need to type `git tag v1.3.x`. Just commit and push to `main`, and the robots will handle the rest.

---
"""

for i, line in enumerate(lines):
    if line.strip() == "## Monitoring & Maintenance":
        lines.insert(i-1, new_content)
        break

with open('docs/05_DEPLOYMENT_PLAN.md', 'w') as f:
    f.writelines(lines)

