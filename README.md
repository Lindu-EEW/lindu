# Lindu.id - IoT Earthquake Early Warning System (EEWS)

Proyek Tesis S2 IoT - Sistem Peringatan Dini Gempa Berbasis Jaringan Sensor Terdistribusi (Edge Computing) dan WebSockets.

## Status Sistem (Versi 2.0 - COMMAND CENTER)
Sistem ini telah dimutakhirkan secara menyeluruh. Versi saat ini menggunakan arsitektur *Enterprise-Grade*:
* **Backend (Konsensus & API):** Python Paho MQTT + Flask REST API. Menggunakan Algoritma Konsensus Fisika (P-Wave Velocity) dan *Center of Energy Refinement*.
* **Broker:** Eclipse Mosquitto (Protokol WebSockets untuk aliran data *Real-Time*).
* **Database:** PostgreSQL / TimescaleDB (Menyimpan log sejarah sensor dan gempa).
* **Frontend:** Dasbor (Command Center) menggunakan **React + Vite** + Tailwind CSS v4 + Leaflet. Di-*serve* via Docker Nginx.
* **Sensor Nodes:** C++ (PlatformIO) untuk perangkat fisik ESP32.

## Struktur Direktori Utama
* `src/server/` : Mesin Konsensus Python (`consensus.py`) dan Simulator Gempa Ekstrem 23-Node (`simulate_e2e.py`).
* `src/dashboard-react/` : Source code Dasbor React. Hasil kompilasi (`dist`) disajikan langsung oleh Nginx.
* `src/esp32_sensor_node/` & `src/esp32_actuator_node/` : Kode sumber mikrokontroler (Tahap selanjutnya).

## Panduan Menjalankan Sistem

Seluruh arsitektur kini telah dibungkus ke dalam **Docker Compose**. Anda tidak perlu lagi menjalankan skrip peladen secara manual.

1. **Jalankan Seluruh Infrastruktur (Backend, Frontend, DB, Broker):**
   ```bash
   docker-compose up -d --build
   ```
   *Dashboard kini bisa diakses di **http://localhost/** secara otomatis (tanpa perlu npm run dev).*

2. **Jalankan Simulasi Uji Coba Gempa (Megathrust Kanto 23-Node):**
   Buka terminal, dan tembakkan skenario simulasi:
   ```bash
   python3 src/server/simulate_e2e.py
   ```

## Fitur Unggulan (React Refactor)
* **Hybrid Data Fetching:** Saat baru dimuat, Dasbor menarik riwayat gempa melalui **REST API (Port 5050)** dari PostgreSQL. Setelah itu, Dasbor murni mengandalkan **WebSockets (Port 9001)** untuk latensi nol milidetik.
* **Geospatial Intelligence:** Peta secara gaib mendeteksi lokasi asali (Tokyo/Jakarta). Titik biru merepresentasikan seluruh *nodes* sensor historis maupun yang sedang aktif.
* **Massive Node UI:** Mendukung hingga puluhan sensor (20+) secara bersamaan tanpa merusak *layout* (*overflow-y-auto* dan Chart.js dinamis).
* **Silent Mode:** Gempa di luar radius bahaya tidak akan memunculkan spanduk merah yang mengganggu, melainkan hanya masuk ke daftar riwayat secara senyap.
