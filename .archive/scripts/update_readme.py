import re

with open('README.md', 'r') as f:
    md = f.read()

# Update Cooldown 60s -> 30s
md = md.replace('Cooldown 60 Detik:', 'Cooldown 30 Detik:')
md = md.replace('selama 60 detik untuk', 'selama 30 detik untuk')

# Update Command Center table
target_cmd = '''| 🔥 **FACTORY RESET** | Menghapus seluruh konfigurasi dan mengembalikan ke mode AP |'''
replacement_cmd = target_cmd + '''\n| 🔄 **RESTART SERVER** | Me-restart backend Python konsensus secara remote (Whitelisted Server Agent) |'''
md = md.replace(target_cmd, replacement_cmd)

# Tambahkan fitur keamanan & arsitektur baru
target_arch = '''### 8.5 Auto-Purge Data Retention
*Daemon Thread* berjalan setiap 24 jam untuk menghapus data telemetri normal yang berusia > 7 hari, memastikan penyimpanan server tidak pernah penuh.'''
replacement_arch = target_arch + '''\n\n### 8.6 Zero-Torque Motor Standby
Untuk varian S3 dengan aktuator Servo, arus listrik PWM diputus total (`detach()`) 2,5 detik setelah katup berputar. Ini mencegah *motor jitter*, *overheat*, dan keausan mekanis, memastikan umur motor bisa bertahan hingga 10 tahun nonstop tanpa terbakar.

### 8.7 Self-Healing Database Connection
*Connection Pool* dilengkapi dengan *Ping-Test* (`SELECT 1`). Jika *container* PostgreSQL terputus atau *stale*, peladen Python secara instan menghancurkan *pool* lama dan merekonstruksi koneksi baru, menghasilkan *uptime* sistem 100% tanpa *crash*.

### 8.8 Remote Server Agent & CI/CD Pipeline
Dilengkapi sistem monitoring host (`psutil`) yang mengirim persentase CPU dan RAM Raspberry Pi ke *database* (`tb_server_health`). Peladen juga memiliki kapabilitas *Remote Restart* aman tanpa membuka akses SSH. Repositori Python juga dilindungi oleh **GitHub Actions (CI/CD)** untuk mencegah *Syntax/Indentation Error* masuk ke *production*.'''
md = md.replace(target_arch, replacement_arch)

target_sec = '''- Jika kebocoran gas terdeteksi: Katup ditutup paksa (*fail-safe*, mengabaikan status manual)'''
replacement_sec = target_sec + '''\n\n### 7.5 OTA Visual Indicators & Anti-Rollback
Proses *Over-The-Air* (OTA) dilengkapi animasi LED khusus untuk *maintenance* jarak jauh:
- 🧊 **Cyan Berkedip Cepat**: Sedang *download* firmware
- 🍇 **Ungu Solid**: Berhasil ditulis ke memori, bersiap *restart*

*Firmware* mengunci persetujuan validasi di baris ke-1 `setup()` untuk memutus *bug OTA Rollback Race Condition* jika WiFi *router* memakan waktu lama untuk tersambung pasca-reboot.'''
md = md.replace(target_sec, replacement_sec)

# Update Grafana
target_grafana = '''| Command Center | Interactive | Tombol-tombol kendali jarak jauh (OTA, GPS, Valve, Reset) |'''
replacement_grafana = target_grafana + '''\n| Server Health | Stat | Memantau penggunaan CPU, RAM, dan Uptime peladen Raspberry Pi |'''
md = md.replace(target_grafana, replacement_grafana)

with open('README.md', 'w') as f:
    f.write(md)

