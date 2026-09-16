import re

with open('src/server/consensus.py', 'r') as f:
    py = f.read()

# 1. Tambahkan import psutil dan sys di awal
target_import = 'import math'
replacement_import = 'import math\nimport psutil\nimport sys\nimport os'
py = py.replace(target_import, replacement_import)

# 2. Tambahkan Thread Telemetry Server
target_retention = '''def db_retention_task():'''
replacement_retention = '''SERVER_BOOT_TIME = time.time()

def server_telemetry_task():
    """Mengirim data CPU dan RAM server secara rutin ke MQTT untuk dipantau di Grafana"""
    while True:
        try:
            if mqtt_client:
                cpu_usage = psutil.cpu_percent(interval=1)
                ram_usage = psutil.virtual_memory().percent
                uptime_hrs = round((time.time() - SERVER_BOOT_TIME) / 3600.0, 2)
                
                payload = {
                    "cpu_percent": cpu_usage,
                    "ram_percent": ram_usage,
                    "uptime_hours": uptime_hrs,
                    "status": "ONLINE"
                }
                mqtt_client.publish("lindu/server/status", json.dumps(payload), retain=True)
        except Exception as e:
            print("[SERVER] Gagal mengirim telemetry server:", e)
        time.sleep(10)

server_telemetry_thread = threading.Thread(target=server_telemetry_task, daemon=True)
server_telemetry_thread.start()

def db_retention_task():'''
py = py.replace(target_retention, replacement_retention)

# 3. Tambahkan Handler Command `restart_server`
target_cmd = '''        if cmd == "trigger_siren":
            print("[+] Menerima perintah MANUAL TRIGGER SIREN!")'''
replacement_cmd = '''        if cmd == "restart_server":
            print("[!!!] Menerima perintah REMOTE RESTART. Server akan mematikan diri dan di-restart oleh Docker.")
            # Kirim status offline sebelum mati
            mqtt_client.publish("lindu/server/status", json.dumps({"status": "RESTARTING", "cpu_percent": 0, "ram_percent": 0, "uptime_hours": 0}), retain=True)
            sys.exit(0)  # Bunuh diri, Docker akan otomatis me-restart script ini
            
        if cmd == "trigger_siren":
            print("[+] Menerima perintah MANUAL TRIGGER SIREN!")'''
py = py.replace(target_cmd, replacement_cmd)

# Tulis kembali
with open('src/server/consensus.py', 'w') as f:
    f.write(py)

