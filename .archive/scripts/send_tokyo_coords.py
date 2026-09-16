import paho.mqtt.client as mqtt
import json
import time

nodes = [
    {"id": "node_3c096f0c", "lat": 35.6762, "lon": 139.6503, "name": "Shinjuku"},
    {"id": "node_acbd13f9", "lat": 35.6580, "lon": 139.7016, "name": "Shibuya"},
    {"id": "node_2418399e", "lat": 35.7100, "lon": 139.8107, "name": "Tokyo Skytree"}
]

client = mqtt.Client()
client.connect("localhost", 1883, 60)
client.loop_start()

for n in nodes:
    payload = {
        "cmd": "set_location",
        "target_node": n["id"],
        "lat": n["lat"],
        "lon": n["lon"]
    }
    client.publish("lindu/actuator/cmd/all", json.dumps(payload))
    print(f"Sent {n['name']} coordinates to {n['id']}")
    time.sleep(1)

client.loop_stop()
client.disconnect()
