with open('src/server/consensus.py', 'r') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "mqtt_# Broadcast" in line:
        lines[i] = "            # Broadcast ke semua kemungkinan topik agar diterima oleh firmware versi lama maupun baru\n"
    elif "mqtt_client.publish(TOPIC_ALARM" in line:
        lines[i] = "            mqtt_client.publish(TOPIC_ALARM, json.dumps(payload))\n"
    elif "mqtt_client.publish(\"lindu/actuator/cmd/all\"" in line:
        lines[i] = "            mqtt_client.publish(\"lindu/actuator/cmd/all\", json.dumps(payload))\n"
    elif "mqtt_client.publish(\"lindu/sensor/cmd/all\"" in line:
        lines[i] = "            mqtt_client.publish(\"lindu/sensor/cmd/all\", json.dumps(payload))\n"
    elif "mqtt_client.publish(f\"lindu/sensor/cmd/{target}\"" in line:
        lines[i] = "            mqtt_client.publish(f\"lindu/sensor/cmd/{target}\", json.dumps(payload))\n"

with open('src/server/consensus.py', 'w') as f:
    f.writelines(lines)

