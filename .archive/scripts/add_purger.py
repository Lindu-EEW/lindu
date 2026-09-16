import re

with open('src/server/consensus.py', 'r') as f:
    py = f.read()

purger_code = '''
# --- DATABASE RETENTION POLICY (AUTO-PURGE) ---
import threading

def db_retention_task():
    """Menghapus data telemetri normal yang lebih tua dari 7 hari agar disk tidak penuh"""
    while True:
        try:
            conn = get_db_connection()
            if conn:
                cur = conn.cursor()
                # Hapus telemetri yang lebih tua dari 7 hari
                cur.execute("DELETE FROM tb_sensor_telemetry WHERE ts < NOW() - INTERVAL '7 days';")
                conn.commit()
                release_db_connection(conn)
                print("[MAINTENANCE] Berhasil menghapus data telemetri lama (>7 hari).")
        except Exception as e:
            print("[MAINTENANCE] Gagal melakukan auto-purge database:", e)
        
        # Jalankan setiap 24 jam sekali
        time.sleep(86400)

# Jalankan Thread Retention
retention_thread = threading.Thread(target=db_retention_task, daemon=True)
retention_thread.start()
# ----------------------------------------------
'''

# We will inject this before the mqtt.Client() initialization
target_hook = "client = mqtt.Client(client_id=\"LinduConsensusServer\")"
py = py.replace(target_hook, purger_code + "\n" + target_hook)

with open('src/server/consensus.py', 'w') as f:
    f.write(py)
