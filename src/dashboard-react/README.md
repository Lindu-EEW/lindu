# Lindu.id Dashboard (React Refactor)

Dasbor ini telah ditulis ulang sepenuhnya menggunakan **React + Vite** sesuai dengan standar industri terkini, memisahkan logika UI menjadi komponen-komponen mandiri.

## Struktur Komponen Utama

* `App.jsx` - Komponen induk yang menyatukan semua elemen.
* `hooks/useMqtt.js` - Mengatur siklus hidup WebSockets MQTT dan menyimpan histori telemetri.
* `components/MapPanel.jsx` - Memanfaatkan `react-leaflet` untuk manajemen Peta yang jauh lebih stabil dari memori.
* `components/HistorySidebar.jsx` - Menampilkan daftar gempa dan merender Accordion yang membungkus grafik secara lokal.
* `components/TelemetryChart.jsx` - Menggunakan `react-chartjs-2` untuk merender telemetri spesifik gempa tanpa membebani DOM utama.
* `components/AlarmBanner.jsx` - Menangani logika jarak (Mode Personal vs Global) dan menghitung ETA kedatangan gelombang merusak secara reaktif.

## Cara Menjalankan

Karena Dasbor ini tidak lagi menggunakan HTML tunggal (Vanilla JS), Anda perlu menjalankan *development server* atau membangunnya (*build*).

1. Buka terminal di folder ini:
   ```bash
   cd src/dashboard-react
   ```
2. Instal dependensi (Jika belum):
   ```bash
   npm install
   ```
3. Jalankan server pengembangan lokal:
   ```bash
   npm run dev
   ```
4. Buka tautan yang muncul (biasanya `http://localhost:5173`) di peramban web Anda.

**Catatan:** Pastikan broker MQTT Mosquitto tetap berjalan di `ws://localhost:9001`!
