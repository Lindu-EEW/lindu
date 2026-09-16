import re

with open('src/server/consensus.py', 'r') as f:
    py = f.read()

# =====================================================
# FIX 1: Tambah cooldown 60 detik agar fire_alarm tidak
# bisa dipanggil berkali-kali untuk gempa yang sama
# =====================================================
target_fire = '''def fire_alarm(client, t1, t2, velocity, time_diff):
    global active_quake
    import time
    active_quake = {'''

replacement_fire = '''last_alarm_time = 0  # Cooldown tracker

def fire_alarm(client, t1, t2, velocity, time_diff):
    global active_quake, last_alarm_time
    import time
    
    # COOLDOWN 60 DETIK: Jika alarm sudah pernah dipicu < 60 detik lalu,
    # JANGAN membuat alarm baru. Biarkan Live Refinement yang bekerja.
    if time.time() - last_alarm_time < 60:
        print("[COOLDOWN] Alarm diabaikan. Gempa ini masih dalam jendela pemurnian 60 detik.")
        return
    
    last_alarm_time = time.time()
    active_quake = {'''

py = py.replace(target_fire, replacement_fire)

# =====================================================
# FIX 2: UPDATE hanya 1 baris terbaru, bukan semua 
# baris dalam 1 menit
# =====================================================
target_update = '''                                UPDATE tb_system_alerts 
                                SET magnitude = %s, radius_km = %s, epi_lat = %s, epi_lon = %s, description = %s, triggering_nodes = %s
                                WHERE time_alert >= NOW() - INTERVAL '1 minute'
                                RETURNING time_alert;'''

replacement_update = '''                                UPDATE tb_system_alerts 
                                SET magnitude = %s, radius_km = %s, epi_lat = %s, epi_lon = %s, description = %s, triggering_nodes = %s
                                WHERE time_alert = (SELECT time_alert FROM tb_system_alerts ORDER BY time_alert DESC LIMIT 1)
                                RETURNING time_alert;'''

py = py.replace(target_update, replacement_update)

with open('src/server/consensus.py', 'w') as f:
    f.write(py)

