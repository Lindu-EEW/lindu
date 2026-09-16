import re

with open('src/server/consensus.py', 'r') as f:
    content = f.read()

# Ubah DB Host fallback
target_db = '''DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "postgres")
DB_NAME = os.getenv("DB_NAME", "lindu_db")'''

replace_db = '''DB_HOST = os.getenv("DB_HOST", "grafana_postgres")
if DB_HOST == "timescaledb": DB_HOST = "grafana_postgres" # auto patch
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "postgres")
DB_NAME = os.getenv("DB_NAME", "lindu_db")'''

# Ubah MQTT fallback
target_mqtt = '''MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))'''

replace_mqtt = '''MQTT_BROKER = os.getenv("MQTT_BROKER", "grafana_mosquitto")
if MQTT_BROKER == "mosquitto": MQTT_BROKER = "grafana_mosquitto" # auto patch
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))'''

if "auto patch" not in content:
    content = content.replace(target_db, replace_db)
    content = content.replace(target_mqtt, replace_mqtt)
    with open('src/server/consensus.py', 'w') as f:
        f.write(content)

