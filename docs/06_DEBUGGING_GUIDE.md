# Buku Saku Panduan Debugging Lindu.id

Panduan ini ditujukan bagi teknisi lapangan atau pengembang untuk melakukan *troubleshooting* secara mandiri jika terjadi anomali pada sistem Lindu.id.

## 1. Kamus LED Diagnostik Cerdas (Sensor Node)
Alat ESP32 dilengkapi sistem visual "NeoPixel" untuk pelaporan status seketika (tanpa perlu membuka serial monitor).

| Warna & Pola LED | Status Sistem | Solusi / Tindakan |
| :--- | :--- | :--- |
| 🟢 **Hijau (Bernafas)** | Normal (Sistem Sehat 100%) | - |
| 🟡 **Kuning (Bernafas)** | Sensor Cuaca (BMP280) Putus | Periksa kabel SDA/SCL pada Pin 4 & 5. |
| 🔴 **Merah (Bernafas)** | Sensor Gempa (LSM6DS3) Putus | Periksa kabel I2C pada Pin 12 & 13. Alat tidak bisa mendeteksi gempa. |
| 🚨 **Merah Cepat (Strobo)** | Kondisi Kritis / Gempa Lokal | Jika tidak ada gempa, berarti KEDUA kabel sensor putus secara bersamaan. |
| 🟤 **Merah Gelap (Kedip)** | Koneksi Putus (Jaringan/Server)| Router Wi-Fi mati, atau IP/Hostname Server MQTT tidak dapat dijangkau. |
| 💖 **Pink (Kedip Pelan)** | Waspada (Getaran Lokal) | Alat mendeteksi getaran (PGA > 0.05g), sedang menunggu konfirmasi dari server. |

## 2. Pemulihan Koneksi Jaringan Tanpa Re-Flash
Jika IP Address server berubah atau router mati, ESP32 akan menggunakan *Captive Portal*. Anda TIDAK PERLU melakukan flash ulang kabel USB.

1. **Reset Alat:** Tekan tombol EN (Reset) pada ESP32. Jika Wi-Fi rumah tidak ditemukan, ESP32 akan masuk ke mode *Access Point*.
2. **Konek via HP:** Buka HP dan hubungkan ke Wi-Fi `Lindu_Setup`.
3. **Login Portal:** Akan muncul layar *login* di HP.
4. **Ubah Server:** Masukkan IP baru, atau lebih disarankan menggunakan mDNS Hostname laptop (contoh: `Likos-MacBook-Air.local`) di kolom *MQTT Server*.
5. Klik **Save**. Alat akan otomatis *restart* dan mencari koneksi baru.

## 3. Pengecekan Database (PostgreSQL)
Jika grafik Grafana tidak muncul, pastikan data berhasil masuk ke database melalui perintah Docker berikut:

**Cek apakah node mengirim telemetri:**
```sql
docker exec grafana_postgres psql -U postgres -d lindu_db -c "SELECT node_id, count(*), max(time) FROM sensor_telemetry GROUP BY node_id;"
```

**Cek apakah sensor hardware melaporkan "rusak":**
```sql
docker exec grafana_postgres psql -U postgres -d lindu_db -c "SELECT DISTINCT ON (node_id) node_id, sensor_ok FROM sensor_status ORDER BY node_id, time DESC;"
```

## 4. Mekanisme OTA (Over-The-Air) & Auto-Rollback
Sistem dapat mengupdate perangkat lunaknya sendiri secara otomatis dari GitHub Releases.
- Jika versi baru ternyata merusak (*Watchdog Crash*), bootloader perangkat keras akan otomatis melakukan **Rollback** ke versi stabil sebelumnya.
- Tag versi yang rusak tersebut akan di-*blacklist* di dalam memori NVS EEPROM agar ESP32 tidak terjebak dalam *boot-loop*.

