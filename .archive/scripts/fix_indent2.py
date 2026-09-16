with open('src/server/consensus.py', 'r') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "mqtt_client.publish(TOPIC_ALARM, json.dumps(payload))" in line and "def send_cmd():" not in line:
        if i > 430 and i < 450:
            lines[i] = "                    mqtt_client.publish(TOPIC_ALARM, json.dumps(payload))\n"

with open('src/server/consensus.py', 'w') as f:
    f.writelines(lines)

