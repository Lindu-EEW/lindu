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

---

## 1. Kebutuhan Perangkat Keras
Setiap Node Lindu membutuhkan komponen berikut:
* **Microcontroller:** ESP32-S3 (atau ESP32 varian standar)
* **Sensor Seismik:** LSM6DS3 (I2C)
* **Sensor Cuaca:** BME280 / BMP280 (I2C)
* **Aktuator:** LED, Buzzer (Active-Low), dan Motor Servo (opsional)

**Skema Kabel (Wiring I2C - ESP32-S3):**
* `SDA` -> GPIO 10
* `SCL` -> GPIO 11
* `Buzzer` -> GPIO 15
* `LED` -> GPIO 16

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
   * Dashboard **"Seismic Monitor"** sudah terkonfigurasi secara otomatis (lengkap dengan Peta Geografis dan *Command Center*).
   * MQTT Broker otomatis berjalan di port `1883`.

---

## 3. Instalasi ESP32 Node (Firmware)

1. **Flash Firmware via PlatformIO:**
   Buka folder `src/esp32_sensor_node` menggunakan VSCode + PlatformIO, lalu klik tombol **Upload**.

2. **Konfigurasi Awal (Captive Portal):**
   * Saat pertama kali menyala, ESP32 akan memancarkan WiFi *Access Point* bernama **`Lindu_Node_XXXX`**.
   * Hubungkan HP/Laptop Anda ke WiFi tersebut.
   * Akan muncul halaman *Captive Portal* secara otomatis.
   * Masukkan **Nama WiFi Rumah Anda**, **Password WiFi**, dan **IP Address Server MQTT** (IP komputer/laptop yang menjalankan Docker).
   * Masukkan Koordinat awal (Latitude & Longitude).
   * Klik **Save**. ESP32 akan *restart* dan terhubung ke *server* Anda.

---

## 4. Menjalankan Mesin Konsensus
Mesin konsensus adalah otak sistem yang mencegah *False Positive* menggunakan perhitungan Fisika Gelombang P-Wave.

1. Masuk ke folder server:
   ```bash
   cd src/server
   ```
2. Install *library* Python:
   ```bash
   pip install -r requirements.txt
   ```
3. Jalankan *engine*:
   ```bash
   python consensus.py
   ```
*(Catatan: Anda juga bisa membungkusnya ke dalam Docker agar berjalan otomatis bersama Grafana).*

---

## 5. Panduan Operasional & Command Center

Sistem Lindu-EEW dilengkapi dengan kendali jarak jauh (OTA & MQTT) yang bisa diakses dari **Grafana Interactive Command Center**.

* **📡 FORCE OTA UPDATE:** 
  Menyuruh semua node mengunduh versi firmware terbaru secara otomatis dari halaman *GitHub Releases* di Organisasi `Lindu-EEW`.
* **📍 SET KOORDINAT BARU:**
  Memungkinkan Anda mengubah titik GPS Node (Latitude & Longitude) secara instan tanpa perlu mencabut alat atau mereset WiFi. Sangat berguna untuk simulasi perambatan gelombang gempa di peta.
* **🔥 FACTORY RESET:**
  Menghapus paksa memori kredensial WiFi dan koordinat di ESP32, lalu mengembalikannya menjadi mode *Access Point* (Lindu_Node_XXXX).
