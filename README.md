# 🌋 Lindu-EEW (Earthquake Early Warning System)

Selamat datang di repositori utama **Lindu-EEW**, sebuah sistem pendeteksi gempa bumi desentralisasi berbasis *Internet of Things* (IoT) dengan algoritma konsensus P-Wave.

Sistem ini terdiri dari 3 komponen utama (submodules):
1. **ESP32 Sensor Node** (`src/esp32_sensor_node`)
2. **Consensus Server & API** (`src/server`)
3. **Grafana & Data Stack** (`prototype/grafana-stack`)

---

## 📋 Daftar Isi
1. [Kebutuhan Perangkat Keras](#1-kebutuhan-perangkat-keras)
2. [Instalasi Server (Docker & Grafana)](#2-instalasi-server-docker--grafana)
3. [Instalasi ESP32 Node (Firmware)](#3-instalasi-esp32-node-firmware)
4. [Menjalankan Mesin Konsensus](#4-menjalankan-mesin-konsensus)
5. [Panduan Operasional & Command Center](#5-panduan-operasional--command-center)
6. [Algoritma Deteksi Gempa](#6-algoritma-deteksi-gempa)
7. [Sistem Keamanan Multi-Layer](#7-sistem-keamanan-multi-layer)
8. [Enterprise-Grade Architecture](#8-enterprise-grade-architecture)
9. [Data Atmosfer (Suhu & Tekanan)](#9-data-atmosfer-suhu--tekanan)
10. [Grafana Dashboard](#10-grafana-dashboard)

---

## 1. Kebutuhan Perangkat Keras

### Varian A: ESP32-S3 (Servo Valve)
| Komponen | Koneksi |
|----------|---------|
| LSM6DS3 (Seismik) | SDA → GPIO 10, SCL → GPIO 11 |
| BME280/BMP280 (Atmosfer) | SDA → GPIO 10, SCL → GPIO 11 (Shared I2C) |
| NeoPixel LED | GPIO 16 |
| Buzzer (Active-Low) | GPIO 15 |
| Servo Motor (Valve) | GPIO 2 |

### Varian B: ESP32 Classic/WROOM (Relay + Gas Sensor)
| Komponen | Koneksi |
|----------|---------|
| LSM6DS3 (Seismik) | SDA → GPIO 18, SCL → GPIO 19 |
| BME280/BMP280 (Atmosfer) | SDA → GPIO 21, SCL → GPIO 22 |
| Relay CH1 (Door Lock) | GPIO 25 |
| Relay CH2 (Gas/Water Valve) | GPIO 26 |
| MQ-2 Gas Sensor | GPIO 34 (Analog) |
| NeoPixel LED | GPIO 16 |
| Buzzer (Active-Low) | GPIO 15 |

---

## 2. Instalasi Server (Docker & Grafana)
Sistem *backend* sangat mudah di-deploy menggunakan Docker.

1. **Masuk ke folder Grafana Stack:**
   ```bash
   cd prototype/grafana-stack
   ```
2. **Jalankan Docker Compose:**
   ```bash
   docker-compose up -d
   ```
3. **Akses Dashboard Grafana:**
   * Buka browser ke `http://localhost:3000`
   * Dashboard **"Seismic Monitor"** sudah terkonfigurasi secara otomatis.
   * MQTT Broker otomatis berjalan di port `1883`.

---

## 3. Instalasi ESP32 Node (Firmware)

1. **Flash Firmware via PlatformIO:**
   Buka folder `src/esp32_sensor_node` menggunakan VSCode + PlatformIO, lalu klik tombol **Upload**.

2. **Konfigurasi Awal (Captive Portal):**
   * Saat pertama kali menyala, ESP32 akan memancarkan WiFi *Access Point* bernama **`Lindu_Node_XXXX`**.
   * Hubungkan HP/Laptop Anda ke WiFi tersebut.
   * Akan muncul halaman *Captive Portal* secara otomatis.
   * Masukkan **Nama WiFi**, **Password WiFi**, **IP Address MQTT Server**, dan **Koordinat GPS**.
   * Klik **Save**. ESP32 akan *restart* dan terhubung ke *server* Anda.

---

## 4. Menjalankan Mesin Konsensus
Mesin konsensus adalah otak sistem yang mencegah *False Positive* menggunakan perhitungan Fisika Gelombang P-Wave.

```bash
cd src/server
pip install -r requirements.txt
python consensus.py
```

*(Catatan: Anda juga bisa membungkusnya ke dalam Docker agar berjalan otomatis bersama Grafana).*

---

## 5. Panduan Operasional & Command Center

Sistem Lindu-EEW dilengkapi dengan kendali jarak jauh (OTA & MQTT) yang bisa diakses dari **Grafana Interactive Command Center**.

| Perintah | Fungsi |
|----------|--------|
| 📡 **FORCE OTA UPDATE** | Menyuruh semua node mengunduh firmware terbaru dari GitHub Releases |
| 📍 **SET KOORDINAT** | Mengubah titik GPS node secara instan via MQTT |
| 🔓 **ENABLE VALVE** | Membuka kunci katup gas/air setelah gempa (Manual Reset) |
| 🔒 **DISABLE VALVE** | Menutup paksa katup gas/air |
| 🚪 **LOCK/UNLOCK DOOR** | Mengunci/membuka solenoid pintu (Varian Classic) |
| 🔥 **FACTORY RESET** | Menghapus seluruh konfigurasi dan mengembalikan ke mode AP |
| 🔄 **RESTART SERVER** | Me-restart backend Python konsensus secara remote (Whitelisted Server Agent) |

---

## 6. Algoritma Deteksi Gempa

### 6.1 Deteksi Lokal (Edge Computing - ESP32)
Setiap node ESP32 secara mandiri menghitung 3 metrik seismik setiap milidetik:

| Metrik | Formula | Fungsi |
|--------|---------|--------|
| **PGA** (Peak Ground Acceleration) | `√(ax² + ay² + az²) / 9.81` | Mengukur kekuatan guncangan dalam satuan G |
| **STA/LTA** (Short-Term Average / Long-Term Average) | `EMA(α=0.1) / EMA(α=0.005)` | Mengukur rasio energi sesaat vs energi latar. Gempa: >2.0, Kaki: <1.5 |
| **Frekuensi Dominan** | Zero-Crossing Rate | Gempa bumi: 1-15 Hz. Hentakan kaki/meja: >20 Hz |

**Gravity Removal:** Vektor gravitasi bumi dihilangkan menggunakan filter EMA (`α=0.002`) yang secara adaptif mengkalibrasi posisi sensor (Flat/Wall Mount).

### 6.2 Konsensus Server (Anti-Hoax 3-Layer)
Peladen Python menerima laporan getaran dari seluruh node dan menerapkan 3 lapis filter ketat:

```
Layer 1: PGA >= 0.12G        → Getaran cukup keras?
Layer 2: STA/LTA >= 2.0      → Energi berkelanjutan (bukan benturan singkat)?
Layer 3: Frekuensi <= 20 Hz  → Gelombang seismik (bukan ketukan sepatu)?
```

Jika **lolos ketiga filter**, data masuk ke *Trigger Buffer* dan menunggu konfirmasi dari node lain.

### 6.3 Validasi Fisika P-Wave
Ketika 2+ node bergetar dalam jendela waktu 60 detik:
- Hitung jarak antar node menggunakan **Haversine Formula**
- Hitung kecepatan rambat: `V = Jarak (km) / Δt (detik)`
- Validasi: `0.5 km/s < V < 25.0 km/s` (Kecepatan P-Wave di kerak bumi)
- Jika node berjarak < 0.1 km (satu ruangan): **Bypass fisika**, langsung validasi

### 6.4 Live Magnitude Refinement (15 Detik)
Setelah alarm pertama terpicu, peladen membuka **Jendela Pemurnian 15 detik**:
- Mengumpulkan data dari **seluruh** node yang aktif
- Menghitung ulang episentrum menggunakan **Weighted Center of Energy** (PGA tertinggi = bobot terbesar)
- Merevisi magnitudo secara *real-time* berdasarkan PGA maksimum absolut
- Menyimpan hasil revisi terakhir ke database (1 baris per event, bukan duplikat)

**Cooldown 30 Detik:** Setelah alarm tercipta, `fire_alarm()` menolak membuat alarm baru selama 30 detik untuk mencegah duplikasi record.

---

## 7. Sistem Keamanan Multi-Layer

### 7.1 Alarm Bertingkat
| Level | Kondisi | Aksi ESP32 |
|-------|---------|-----------|
| 🩷 **Lokal (Pink)** | 1 node: PGA > 0.12G | LED berkedip Pink + Tick pelan. Menunggu konfirmasi server |
| 🔴 **Global (Merah)** | 2+ node: Konsensus tercapai | Sirine keras 15 detik + LED Merah + Katup TERKUNCI + Pintu TERBUKA |
| 🐺 **Lone Wolf** | Server OFFLINE + PGA > 0.60G | ESP32 mengambil alih: Sirine + Katup + Pintu secara MANDIRI |

### 7.2 Lone Wolf Mode (Offline Fail-Safe)
Jika koneksi ke MQTT server terputus dan ESP32 mendeteksi getaran yang **amat sangat brutal** (PGA > 0.60G, setara gempa merobohkan bangunan), alat akan mengaktifkan **mode bertahan hidup mandiri**:
- Membunyikan sirine merah 15 detik
- Mengunci katup gas/air (NVS Persistent)
- Membuka pintu untuk evakuasi (Varian Classic)

Ini adalah garis pertahanan terakhir ketika seluruh infrastruktur internet runtuh akibat gempa.

### 7.3 NVS Persistence (Anti-Blackout)
Status katup pengaman disimpan di memori *Non-Volatile Storage* (EEPROM). Skenario:
1. Gempa terjadi → Katup terkunci → `actPrefs.putBool("valve_locked", true)`
2. Listrik PLN padam (ESP32 mati total)
3. Listrik menyala kembali → ESP32 membaca NVS → Katup **tetap terkunci**
4. Hanya bisa dibuka secara manual melalui Grafana Command Center

### 7.4 Deteksi Kebocoran Gas (Varian Classic)
Sensor MQ-2 pada ESP32 Classic secara terus-menerus memantau kadar gas di udara:
- **Warm-up delay 30 detik** setelah boot untuk kalibrasi akurasi sensor
- Jika kebocoran gas terdeteksi: Katup ditutup paksa (*fail-safe*, mengabaikan status manual)

### 7.5 OTA Visual Indicators & Anti-Rollback
Proses *Over-The-Air* (OTA) dilengkapi animasi LED khusus untuk *maintenance* jarak jauh:
- 🧊 **Cyan Berkedip Cepat**: Sedang *download* firmware
- 🍇 **Ungu Solid**: Berhasil ditulis ke memori, bersiap *restart*

*Firmware* mengunci persetujuan validasi di baris ke-1 `setup()` untuk memutus *bug OTA Rollback Race Condition* jika WiFi *router* memakan waktu lama untuk tersambung pasca-reboot.

---

## 8. Enterprise-Grade Architecture

### 8.1 Dual-Core FreeRTOS (Anti-Freeze)
| Core | Tugas | Prioritas |
|------|-------|-----------|
| **Core 0** | WiFi, MQTT, OTA Download | Normal |
| **Core 1** | Pembacaan Sensor LSM6DS3 (1000 Hz), Alarm LED & Buzzer | Tinggi |

Pembaharuan OTA dikerjakan sepenuhnya di latar belakang menggunakan `xTaskCreatePinnedToCore()`. Sensor gempa **tidak pernah berhenti** walau sedang mengunduh firmware 1MB.

### 8.2 Zero-Heap Memory Allocation
Seluruh pembuatan payload JSON dan MQTT menggunakan Static C-String (`char buffer[512]` dan `snprintf`), memastikan 0% *Heap Fragmentation*. ESP32 dapat beroperasi bertahun-tahun tanpa mengalami *Crash* kehabisan RAM.

### 8.3 Millisecond Physics Precision
Perekaman timestamp menggunakan `gettimeofday()` dari `<sys/time.h>` untuk mendapatkan presisi milidetik absolut (contoh: `1700000001.452`). Perhitungan kecepatan P-Wave di peladen akurat hingga hitungan meter.

### 8.4 PostgreSQL Connection Pooling
Peladen Python menerapkan `psycopg2.pool.ThreadedConnectionPool` (1-20 koneksi) untuk menangani ribuan paket telemetri per detik saat gempa tanpa membuat database *overload*.

### 8.5 Auto-Purge Data Retention
*Daemon Thread* berjalan setiap 24 jam untuk menghapus data telemetri normal yang berusia > 7 hari, memastikan penyimpanan server tidak pernah penuh.

### 8.6 Zero-Torque Motor Standby
Untuk varian S3 dengan aktuator Servo, arus listrik PWM diputus total (`detach()`) 2,5 detik setelah katup berputar. Ini mencegah *motor jitter*, *overheat*, dan keausan mekanis, memastikan umur motor bisa bertahan hingga 10 tahun nonstop tanpa terbakar.

### 8.7 Self-Healing Database Connection
*Connection Pool* dilengkapi dengan *Ping-Test* (`SELECT 1`). Jika *container* PostgreSQL terputus atau *stale*, peladen Python secara instan menghancurkan *pool* lama dan merekonstruksi koneksi baru, menghasilkan *uptime* sistem 100% tanpa *crash*.

### 8.8 Remote Server Agent & CI/CD Pipeline
Dilengkapi sistem monitoring host (`psutil`) yang mengirim persentase CPU dan RAM Raspberry Pi ke *database* (`tb_server_health`). Peladen juga memiliki kapabilitas *Remote Restart* aman tanpa membuka akses SSH. Repositori Python juga dilindungi oleh **GitHub Actions (CI/CD)** untuk mencegah *Syntax/Indentation Error* masuk ke *production*.

---

## 9. Data Atmosfer (Suhu & Tekanan)

Sensor BME280/BMP280 mengumpulkan data suhu dan tekanan barometrik secara paralel sebagai **data lingkungan komplementer**. Saat ini data atmosfer **tidak digunakan** dalam algoritma deteksi gempa, melainkan:

- **Ditampilkan** di dashboard Grafana sebagai monitoring cuaca sekunder
- **Disimpan** ke database untuk analisis korelasi pasca-gempa
- **Potensi pengembangan:** Tekanan barometrik tetap akurat meskipun sensor ditempatkan di dalam ruangan (dinding rumah tidak kedap udara). Pada iterasi berikutnya, penurunan tekanan mendadak (1-3 hPa) berpotensi digunakan untuk deteksi gelombang infrasonik pra-tsunami

---

## 10. Grafana Dashboard

Dashboard **"Seismic Monitor"** menyediakan panel-panel berikut:

| Panel | Tipe | Fungsi |
|-------|------|--------|
| Active Nodes | Stat | Jumlah node online dalam 5 menit terakhir |
| Live Fleet Status | Table | Status online/offline, firmware, pose, dan tilt setiap node |
| PGA Gauge | Gauge | Speedometer visual kekuatan guncangan real-time (Hijau → Merah Pekat) |
| Frekuensi Dominan | Time Series | Grafik frekuensi getaran (< 15 Hz = gempa, > 20 Hz = noise) |
| Seismogram Live | Time Series | Grafik gelombang guncangan 3D secara real-time |
| Rasio STA/LTA | Time Series | Grafik rasio energi validasi gempa |
| Temperature | Time Series | Suhu lingkungan dari BME280/BMP280 |
| Barometric Pressure | Time Series | Tekanan atmosfer dari BME280/BMP280 |
| Log Gempa Tervalidasi | Table | Riwayat gempa terdeteksi: Waktu (JST), Magnitudo, Klasifikasi, Radius, Jumlah Node |
| Valve Status | Table | Status katup gas/air setiap node |
| Command Center | Interactive | Tombol-tombol kendali jarak jauh (OTA, GPS, Valve, Reset) |
| Server Health | Stat | Memantau penggunaan CPU, RAM, dan Uptime peladen Raspberry Pi |

**Auto-refresh:** Dashboard menyegarkan data setiap 5 detik.

---

## 📜 Lisensi

Proyek ini dikembangkan sebagai bagian dari mata kuliah **Internet of Things** di bawah bimbingan **Suryadiputra Liawatimena**.

© 2026 Lindu-EEW Team — Group 9
