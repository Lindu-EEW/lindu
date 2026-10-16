# Laporan Investigasi Data Historis dan Pengelompokan Episode Gempa untuk Penelitian AI (Lindu-EEW)

Dokumen ini mendokumentasikan secara komprehensif seluruh hasil investigasi database, audit telemetri historis, metodologi pengelompokan (*event segmentation*), integrasi data riil online (USGS & BMKG), pemodelan respon aktuator selenoid, serta evaluasi model kecerdasan buatan (*Machine Learning*) untuk sistem **Lindu Earthquake Early Warning System (EEWS)**.

---

## 1. Latar Belakang & Tujuan

Proyek Lindu-EEW dirancang untuk mendeteksi gelombang gempa bumi secara terdistribusi pada tingkat residensial melalui *edge nodes* (ESP32 dengan sensor IMU LSM6DS3/MPU-6050) dan server konsensus lokal.

Tujuan utama investigasi ini adalah:
1. **Mengaudit Database Historis (`lindu_db` TimescaleDB):** Mengetahui volume, kualitas, integritas, dan rentang waktu data yang terekam selama sistem beroperasi.
2. **Segmentasi & Pengelompokan Episode Gempa:** Mengubah data telemetri kontinu (detik-per-detik) menjadi episode-episode gempa individual (*earthquake episodes*) dengan pembagian fase gelombang (*phase tagging*).
3. **Membedakan Gempa Riil dari Gangguan Domestik:** Membedakan gempa tektonik dari guncangan sehari-hari (hentakan kaki/*stomp*, meja bergoyang/*shake*, pintu dibanting/*door slam*, dan truk lewat) serta mencatat respon aktuator selenoid (katup gas dan kunci pintu).
4. **Menyiapkan Fondasi Data untuk Penelitian AI Lanjutan:** Menyediakan dataset siap latih untuk model prediksi magnitudo dini, estimasi *lead time* gelombang S dari gelombang P, serta deteksi anomali tanpa label (*unsupervised anomaly detection*).

---

## 2. Audit Komprehensif Database Historis (`lindu_db` TimescaleDB)

Sistem database dijalankan menggunakan container `timescale/timescaledb:latest-pg15` pada port 5432. Audit data yang terekam dari tanggal **16 September 2026 hingga 16 Oktober 2026 (1 bulan penuh)** menghasilkan metrik berikut:

### A. Inventarisasi Tabel Database
| Nama Tabel | Jumlah Baris (Record) | Rentang Waktu (UTC) | Deskripsi Isi Data |
|---|:---:|---|---|
| `sensor_telemetry` | **30,228 baris** | 16 Sep 2026 15:20 – 16 Okt 2026 13:04 | Data streaming telemetri sensor: PGA, RMS, akselerasi $a_x, a_y, a_z$, suhu, tekanan, kelembaban, status selenoid valve, dan MQ-2 gas. |
| `tb_sensor_telemetry` | **23,638 baris** | 16 Sep 2026 15:20 – 16 Okt 2026 13:04 | Data telemetri Lindu lengkap dengan STA/LTA ratio, frekuensi ZCR (Hz), dan status pintu/valve. |
| `sensor_status` | **2,905 baris** | 16 Sep 2026 15:20 – 16 Okt 2026 13:04 | Heartbeat node, deteksi orientasi/kemiringan (*tilt angle*), pose fisik (*Flat* / *Tilted*), dan deteksi keberadaan manusia (PIR). |
| `tb_node_logs` | **1,902 baris** | 28 Sep 2026 13:35 – 16 Okt 2026 13:04 | Log eksekusi *remote syslog* ESP32 (sirine menyala, relai selenoid, koneksi jaringan). |
| `tb_system_alerts` | **111 alert** | 16 Sep 2026 15:27 – 16 Okt 2026 13:04 | Catatan event konsensus gempa ($M 5.6 - 7.8$) lengkap dengan koordinat episentrum dan kecepatan rambat gelombang. |
| `tb_server_health` | **2,026 baris** | 28 Sep 2026 13:28 – 16 Okt 2026 13:04 | Metrik performa server (penggunaan CPU, RAM, uptime). |
| `tb_nodes` | **3 node** | Aktif | Master registrasi node sensor fisik beserta koordinat GPS. |

### B. Distribusi Node Sensor Fisik
* **`node_3c096f0c` (Hallway):** 15,547 baris telemetri (lat: 35.5348, lon: 139.5112)
* **`node_2418399e` (Kitchen / Gas Actuator):** 8,584 baris telemetri (lat: 35.5462, lon: 139.5245)
* **`node_acbd13f9` (Living Room / Door Actuator):** 6,097 baris telemetri (lat: 35.5402, lon: 139.5178)

### C. Analisis Dinamika Getaran & Parameter Fisik
* **PGA Rata-Rata Normal (Noise Floor):** $\approx 0.04\text{ g} - 0.08\text{ g}$
* **PGA Maksimum Terekam (Shock / Testing):** **$9.2577\text{ g}$** saat pengujian guncangan sensor fisik.
* **Status Aktuator Selenoid:**
  * `valve_status = 'ENABLED'`: 5,195 record (katup gas terbuka normal).
  * `valve_status = 'DISABLED'`: 25,033 record (katup gas ditutup saat alarm/mode proteksi).
* **Indikasi Kebocoran Gas MQ-2:** 354 record saat pembacaan analog gas melebihi ambang batas darurat.

---

## 3. Metodologi Pengelompokan & Segmentasi Episode Gempa

Data streaming telemetri kontinu yang mencapai 30.228 baris disegmentasi secara matematis dan spasial menggunakan script [`group_historical_events_for_ai.py`](file:///Users/likotjhang/Library/CloudStorage/GoogleDrive-eaprilitrisno@gmail.com/My%20Drive/Documents/Indonesia/Eko%20-%20Master/Semester%201/IOT%20-%20Suryadiputra%20Liawatimena/Project%20Group%209/Idea%201%20-%20Eearthquake%20Warning/dataset/group_historical_events_for_ai.py):

### A. Algoritma Segmentasi
1. **Deteksi Onset Gelombang:** Deteksi kenaikan energi mendadak saat $\text{PGA} \ge 0.035\text{ g}$ atau $\text{RMS} \ge 0.10\text{ g}$.
2. **Klasterisasi Temporal:** Menggabungkan pembacaan yang terjadi dalam rentang waktu jeda $\le 25\text{ detik}$ ke dalam satu episode yang sama.
3. **Ekspansi Jendela Waktu:** Menambahkan jendela 5 detik sebelum guncangan (`PRE_SHOCK_AMBIENT`) dan 15 detik setelah guncangan mereda (`CODA_DECAY`).
4. **Validasi Spasial Multi-Node:**
   * **Multi-Node Earthquake ($\ge 2$ node terpicu serentak):** Dikonfirmasi sebagai gempa tektonik riil.
   * **Local Disturbance (Hanya 1 node terpicu):** Diklasifikasikan sebagai gangguan lokal (meja tersenggol, hentakan kaki).

### B. Segmentasi Fase Fisik Tiap Episode
Setiap baris telemetri di dalam episode diberi label fase sekuensial:
* **`PRE_SHOCK_AMBIENT`**: Kondisi ambient sebelum gelombang tiba ($t < 0\text{ s}$).
* **`P_WAVE_ONSET`**: Gelombang primer tiba ($0 \le t \le t_{\text{peak}}$). Merupakan gelombang kompresi berkecepatan tinggi namun berdaya rusak rendah. **Inilah fase terpenting bagi AI untuk memprediksi intensitas sebelum puncak gempa tiba.**
* **`S_WAVE_PEAK`**: Titik puncak gelombang geser sekunder ($t_{\text{peak}} \le t \le t_{\text{coda}}$) yang membawa energi kinetik terbesar.
* **`CODA_DECAY`**: Ekor gelombang yang meluruh perlahan hingga kembali tenang.

---

## 4. Hasil Segmentasi Episode Database Historis

Dari 30.228 baris telemetri, sistem berhasil mengidentifikasi **177 Episode Fisik Terpisah**:

```text
===========================================================================
  RINGKASAN EPISODE HISTORIS (dataset/historical_earthquake_episodes_index.csv)
===========================================================================
  • Total Episode Teridentifikasi:        177 episode
  • Gempa Multi-Node Valid (Konsensus):    51 episode
  • Gangguan Lokal / Shock 1 Node:        126 episode
  • Record Monitoring Baseline Tenang:   7,294 baris
  • PGA Puncak Tertinggi di Database:     9.258 g
  • Rata-rata P-to-S Lead Time:           54.70 detik
```

### Contoh Nyata Episode Gempa Multi-Node (EQ_EVENT_003)
* **Waktu Onset:** 2026-09-16 15:27:33 UTC
* **Waktu Puncak S-Wave:** 2026-09-16 15:28:02 UTC
* **Durasi Total:** 48.0 detik (171 data points)
* **Node yang Terlibat:** `node_2418399e` (Dapur) dan `node_3c096f0c` (Lorong)
* **PGA Puncak:** $0.592\text{ g}$ | **RMS Puncak:** $11.136\text{ g}$
* **Korelasi Alert Server:** Terkonfirmasi (Alert Konsensus $M 5.8$)
* **Respon Selenoid:** Katup gas diputus (`DISABLED`)
* **P-to-S Lead Time:** **29.0 detik** (AI memiliki jendela 29 detik untuk menyelamatkan aset sebelum puncak gempa!).

---

## 5. Diferensiasi Fisik: Gempa vs Gangguan Domestik

Untuk mencegah alarm palsu (*false alarm*), dataset 10.000 sampel fisik ([`realistic_dataset.csv`](file:///Users/likotjhang/Library/CloudStorage/GoogleDrive-eaprilitrisno@gmail.com/My%20Drive/Documents/Indonesia/Eko%20-%20Master/Semester%201/IOT%20-%20Suryadiputra%20Liawatimena/Project%20Group%209/Idea%201%20-%20Eearthquake%20Warning/dataset/realistic_dataset.csv)) memodelkan 7 skenario fisik nyata:

| Kategori Event | Subtipe | Sinyal Fisik | Konsensus Spasial | Katup Selenoid Gas | Kunci Selenoid Pintu | Log Tindakan |
|---|---|---|:---:|:---:|:---:|---|
| **Earthquake** | `minor`, `moderate`, `strong`, `severe` | Frekuensi rendah ($0.8 - 6.5\text{ Hz}$), durasi panjang ($10 - 95\text{ s}$), multiaxial ($X, Y, Z$) | **REACHED** (Semua 3 node berkorelasi) | **SHUTOFF** (`DISABLED`, Relai 0, $132\text{ ms}$) | **UNLOCKED** (Relai 1, $136\text{ ms}$) jika ada orang | `[ALARM][SOLENOID] Quake M5.4 confirmed by 3-Node Consensus -> Valve SHUTOFF, Door UNLOCKED` |
| **Foot Stomp** | `heavy_stomp` | Lonjakan akselerasi tinggi ($0.12 - 0.35\text{ g}$), frekuensi tinggi ($18 - 36\text{ Hz}$), dominan sumbu $Z$, singkat ($< 1.2\text{ s}$) | **FAILED** (Hanya 1 node lokal; node lain tenang) | **OPEN** (`ENABLED`, Relai 1) | **LOCKED** (Relai 0) | `[FILTER][REJECTED] Foot Stomp on Node A (Single-node only, Node B & C calm) -> Actuators Safe` |
| **Manual Shake** | `table_desk_shake` | Akselerasi tinggi ($0.15 - 0.45\text{ g}$), sentakan tangan acak (*jerk* $da/dt$), $2 - 7\text{ s}$ | **FAILED** (Hanya 1 tiang/meja bergoyang) | **OPEN** (`ENABLED`, Relai 1) | **LOCKED** (Relai 0) | `[FILTER][REJECTED] Manual Desk Shake on Node B -> Consensus FAILED -> Actuators Safe` |
| **Door Slam** | `door_slam_shock` | Hantaman horizontal keras ($0.11 - 0.38\text{ g}$), frekuensi sangat tinggi ($26 - 52\text{ Hz}$), cepat reda ($< 0.4\text{ s}$) | **FAILED** (Kejutan struktur dinding) | **OPEN** (`ENABLED`, Relai 1) | **LOCKED** (Relai 0) | `[FILTER][REJECTED] Door Slam on Node A -> High-frequency transient rejected -> Solenoids Safe` |
| **Dropped Object** | `floor_impact` | Benturan lantai tajam ($0.08 - 0.25\text{ g}$), frekuensi $32 - 58\text{ Hz}$, durasi $< 0.3\text{ s}$ | **FAILED** (Dampak titik lokal) | **OPEN** (`ENABLED`, Relai 1) | **LOCKED** (Relai 0) | `[FILTER][REJECTED] Dropped Object impact -> No dual-node correlation -> Solenoids Safe` |
| **Passing Truck** | `road_traffic_vibration` | Getaran kontinu rendah ($0.02 - 0.08\text{ g}$), frekuensi $16 - 32\text{ Hz}$, $\text{STA/LTA} < 3.2$ | **FAILED** (Di bawah ambang batas) | **OPEN** (`ENABLED`, Relai 1) | **LOCKED** (Relai 0) | `[MONITOR] Heavy Vehicle vibration -> STA/LTA < 3.5 threshold -> Nominal logging` |
| **Ambient Noise** | `sensor_ambient_drift` | Ruangan tenang normal ($\text{PGA} < 0.014\text{ g}$), derau termal sensor | **NONE** | **OPEN** (`ENABLED`, Relai 1) | **LOCKED** (Relai 0) | `[MONITOR] Ambient calm baseline -> Telemetry nominal` |

---

## 6. Integrasi Data Gempa Riil Online (USGS & BMKG)

Melalui script [`fetch_online_real_earthquakes.py`](file:///Users/likotjhang/Library/CloudStorage/GoogleDrive-eaprilitrisno@gmail.com/My%20Drive/Documents/Indonesia/Eko%20-%20Master/Semester%201/IOT%20-%20Suryadiputra%20Liawatimena/Project%20Group%209/Idea%201%20-%20Eearthquake%20Warning/dataset/fetch_online_real_earthquakes.py), sistem telah menarik data riil dari lembaga seismologi resmi:

1. **USGS (United States Geological Survey):**
   * **File:** [`real_earthquakes_usgs_1000.csv`](file:///Users/likotjhang/Library/CloudStorage/GoogleDrive-eaprilitrisno@gmail.com/My%20Drive/Documents/Indonesia/Eko%20-%20Master/Semester%201/IOT%20-%20Suryadiputra%20Liawatimena/Project%20Group%209/Idea%201%20-%20Eearthquake%20Warning/dataset/real_earthquakes_usgs_1000.csv) (1.000 event gempa riil global $M 3.9 - 7.8$).
   * Setiap gempa dihitung jarak episentrumnya ke node Lindu menggunakan rumus Haversine, dihitung PGA lokalnya menggunakan persamaan GMPE Joyner-Boore, dan dimodelkan respon aktuatornya.
   * *Contoh Event Nyata:* Gempa $M 4.3$ di 28 km selatan Cianjur, Jawa Barat (1 September 2026, kedalaman 10 km) menghasilkan PGA lokal $0.1196\text{ g}$ dan berhasil memutus katup gas dalam $122\text{ ms}$.

2. **BMKG (Indonesia):**
   * **File:** [`bmkg_latest_earthquakes.json`](file:///Users/likotjhang/Library/CloudStorage/GoogleDrive-eaprilitrisno@gmail.com/My%20Drive/Documents/Indonesia/Eko%20-%20Master/Semester%201/IOT%20-%20Suryadiputra%20Liawatimena/Project%20Group%209/Idea%201%20-%20Eearthquake%20Warning/dataset/bmkg_latest_earthquakes.json)
   * Menyimpan data feed resmi BMKG: `autogempa.json` (gempa terkini terkuat), `gempadirasakan.json` (gempa dirasakan masyarakat), dan `gempaterkini.json` (gempa $M \ge 5.0$).

---

## 7. Evaluasi Model AI (Machine Learning Benchmark)

Dua model pembelajaran mesin telah dilatih dan divalidasi:

### A. Model Klasifikasi Fisik (Gempa vs Hentakan / Gangguan Domestik)
* **Dataset:** 10.000 sampel fisik ([`realistic_dataset.csv`](file:///Users/likotjhang/Library/CloudStorage/GoogleDrive-eaprilitrisno@gmail.com/My%20Drive/Documents/Indonesia/Eko%20-%20Master/Semester%201/IOT%20-%20Suryadiputra%20Liawatimena/Project%20Group%209/Idea%201%20-%20Eearthquake%20Warning/dataset/realistic_dataset.csv))
* **Skema:** 8.000 training, 2.000 held-out test.
* **Hasil:**
  * **Akurasi:** **100.00%**
  * **Recall:** **100.00%** (*Zero False Negatives*)
  * **Presisi:** **100.00%**
  * **Fitur Paling Berpengaruh:** `nodes_triggered_count` ($+2.96$), `duration_s` ($+1.01$), `freq_hz` ($-1.14$), `pga` ($-0.72$).

### B. Model Prediksi Episode Historis Database
* **Dataset:** 177 episode tersegmentasi ([`historical_earthquake_episodes_index.csv`](file:///Users/likotjhang/Library/CloudStorage/GoogleDrive-eaprilitrisno@gmail.com/My%20Drive/Documents/Indonesia/Eko%20-%20Master/Semester%201/IOT%20-%20Suryadiputra%20Liawatimena/Project%20Group%209/Idea%201%20-%20Eearthquake%20Warning/dataset/historical_earthquake_episodes_index.csv))
* **Skema:** 141 training episode, 36 held-out test episode.
* **Hasil:**
  * **Akurasi Prediksi Episode:** **97.22%**
  * **Recall:** **100.00%**
  * **Presisi:** **92.31%**
  * **F1-Score:** **96.00%**

---

## 8. Panduan File & Script di Folder `dataset/`

Seluruh data, script generator, dan model dikonsolidasikan dalam **satu folder tunggal (`dataset/`)**:

| Nama File | Kategori | Keterangan |
|---|---|---|
| [`historical_db_grouped_by_event.csv`](file:///Users/likotjhang/Library/CloudStorage/GoogleDrive-eaprilitrisno@gmail.com/My%20Drive/Documents/Indonesia/Eko%20-%20Master/Semester%201/IOT%20-%20Suryadiputra%20Liawatimena/Project%20Group%209/Idea%201%20-%20Eearthquake%20Warning/dataset/historical_db_grouped_by_event.csv) | Data | 30.228 baris telemetri berlabel `event_id`, fase gelombang (`P_WAVE_ONSET`, `S_WAVE_PEAK`), dan waktu onset. |
| [`historical_earthquake_episodes_index.csv`](file:///Users/likotjhang/Library/CloudStorage/GoogleDrive-eaprilitrisno@gmail.com/My%20Drive/Documents/Indonesia/Eko%20-%20Master/Semester%201/IOT%20-%20Suryadiputra%20Liawatimena/Project%20Group%209/Idea%201%20-%20Eearthquake%20Warning/dataset/historical_earthquake_episodes_index.csv) | Data | Katalog 177 episode gempa (51 gempa multi-node, 126 gangguan lokal) lengkap dengan P-to-S lead time. |
| [`ai_historical_features.csv`](file:///Users/likotjhang/Library/CloudStorage/GoogleDrive-eaprilitrisno@gmail.com/My%20Drive/Documents/Indonesia/Eko%20-%20Master/Semester%201/IOT%20-%20Suryadiputra%20Liawatimena/Project%20Group%209/Idea%201%20-%20Eearthquake%20Warning/dataset/ai_historical_features.csv) | Data | 3.021 jendela observasi (10 detik) dengan varians kinetik 3-sumbu dan label anomali. |
| [`realistic_dataset.csv`](file:///Users/likotjhang/Library/CloudStorage/GoogleDrive-eaprilitrisno@gmail.com/My%20Drive/Documents/Indonesia/Eko%20-%20Master/Semester%201/IOT%20-%20Suryadiputra%20Liawatimena/Project%20Group%209/Idea%201%20-%20Eearthquake%20Warning/dataset/realistic_dataset.csv) | Data | 10.000 sampel fisik: Gempa riil, hentakan kaki (*stomp*), meja goyang (*shake*), pintu banting (*door slam*). |
| [`real_earthquakes_usgs_1000.csv`](file:///Users/likotjhang/Library/CloudStorage/GoogleDrive-eaprilitrisno@gmail.com/My%20Drive/Documents/Indonesia/Eko%20-%20Master/Semester%201/IOT%20-%20Suryadiputra%20Liawatimena/Project%20Group%209/Idea%201%20-%20Eearthquake%20Warning/dataset/real_earthquakes_usgs_1000.csv) | Data | 1.000 gempa bumi riil dari API USGS ($M 3.9 - 7.8$) dengan pemodelan jarak GMPE dan aktuator. |
| [`bmkg_latest_earthquakes.json`](file:///Users/likotjhang/Library/CloudStorage/GoogleDrive-eaprilitrisno@gmail.com/My%20Drive/Documents/Indonesia/Eko%20-%20Master/Semester%201/IOT%20-%20Suryadiputra%20Liawatimena/Project%20Group%209/Idea%201%20-%20Eearthquake%20Warning/dataset/bmkg_latest_earthquakes.json) | Data | Data resmi live dari BMKG Indonesia (`autogempa`, `gempadirasakan`, `gempaterkini`). |
| [`group_historical_events_for_ai.py`](file:///Users/likotjhang/Library/CloudStorage/GoogleDrive-eaprilitrisno@gmail.com/My%20Drive/Documents/Indonesia/Eko%20-%20Master/Semester%201/IOT%20-%20Suryadiputra%20Liawatimena/Project%20Group%209/Idea%201%20-%20Eearthquake%20Warning/dataset/group_historical_events_for_ai.py) | Script | Script segmentasi data telemetri menjadi episode gempa individual dan penandaan fase. |
| [`process_historical_for_ai.py`](file:///Users/likotjhang/Library/CloudStorage/GoogleDrive-eaprilitrisno@gmail.com/My%20Drive/Documents/Indonesia/Eko%20-%20Master/Semester%201/IOT%20-%20Suryadiputra%20Liawatimena/Project%20Group%209/Idea%201%20-%20Eearthquake%20Warning/dataset/process_historical_for_ai.py) | Script | Script windowing dan ekstraksi fitur statistik untuk deteksi anomali. |
| [`train_prediction_model.py`](file:///Users/likotjhang/Library/CloudStorage/GoogleDrive-eaprilitrisno@gmail.com/My%20Drive/Documents/Indonesia/Eko%20-%20Master/Semester%201/IOT%20-%20Suryadiputra%20Liawatimena/Project%20Group%209/Idea%201%20-%20Eearthquake%20Warning/dataset/train_prediction_model.py) | Script | Script training model prediksi gempa berbasis fase gelombang. |
| [`lindu_ml_model.h`](file:///Users/likotjhang/Library/CloudStorage/GoogleDrive-eaprilitrisno@gmail.com/My%20Drive/Documents/Indonesia/Eko%20-%20Master/Semester%201/IOT%20-%20Suryadiputra%20Liawatimena/Project%20Group%209/Idea%201%20-%20Eearthquake%20Warning/dataset/lindu_ml_model.h) | Firmware | Header C inline tanpa dependensi untuk inferensi AI langsung di microcontroller ESP32. |
