with open('src/server/consensus.py', 'r') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "publish(TOPIC_ALARM, json.dumps(alarm_payload))" in line:
        lines[i] = """    # Broadcast alarm ke semua kemungkinan topik sensor dan aktuator
    client.publish(TOPIC_ALARM, json.dumps(alarm_payload))
    client.publish("lindu/actuator/cmd/all", json.dumps(alarm_payload))
    client.publish("lindu/sensor/cmd/all", json.dumps(alarm_payload))
"""
    elif "publish(TOPIC_ALARM, json.dumps(update_payload))" in line:
        lines[i] = """                    mqtt_client.publish(TOPIC_ALARM, json.dumps(update_payload))
                    mqtt_client.publish("lindu/actuator/cmd/all", json.dumps(update_payload))
                    mqtt_client.publish("lindu/sensor/cmd/all", json.dumps(update_payload))
"""

with open('src/server/consensus.py', 'w') as f:
    f.writelines(lines)

