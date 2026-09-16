import paho.mqtt.client as mqtt
import json

def on_connect(client, userdata, flags, rc):
    client.subscribe("lindu/sensor/+/telemetry")

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        print(f"[{msg.topic}] Temp: {data.get('temperature')} C | Pres: {data.get('pressure')} hPa")
    except Exception as e:
        print(e)

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect("localhost", 1883, 60)
client.loop_start()
import time
time.sleep(5)
client.loop_stop()
