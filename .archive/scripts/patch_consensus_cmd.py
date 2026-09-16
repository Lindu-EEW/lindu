with open('src/server/consensus.py', 'r') as f:
    code = f.read()

target_str = "mqtt_client.publish(TOPIC_ALARM, json.dumps(payload))"
replacement_str = """# Broadcast ke semua kemungkinan topik agar diterima oleh firmware versi lama maupun baru
        mqtt_client.publish(TOPIC_ALARM, json.dumps(payload))
        mqtt_client.publish("lindu/actuator/cmd/all", json.dumps(payload))
        mqtt_client.publish("lindu/sensor/cmd/all", json.dumps(payload))
        mqtt_client.publish(f"lindu/sensor/cmd/{target}", json.dumps(payload))"""

code = code.replace(target_str, replacement_str)

with open('src/server/consensus.py', 'w') as f:
    f.write(code)

