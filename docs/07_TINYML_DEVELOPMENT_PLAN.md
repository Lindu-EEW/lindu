# 🧠 Lindu EEW: TinyML Development & Benchmarking Plan
**Multi-Model Seismology Machine Learning for ESP32 Edge Computing**

---

## 📌 Ringkasan Eksekutif & Tujuan

Dokumen ini merinci rencana komprehensif implementasi **TinyML (Edge AI)** untuk sistem Peringatan Dini Gempa Bumi (*Earthquake Early Warning* - EEW) pada proyek **Lindu**. 

Tujuan utama dari inisiatif ini adalah:
1. **Mengembangkan dan membandingkan beberapa model Machine Learning** (SVM, Random Forest, MLP/ANN, 1D-CNN, dan Logistic Regression) untuk klasifikasi getaran (*Quake* vs *Ambient Noise* / *Human Disturbance*).
2. **Melakukan Data Cleaning & Feature Engineering** dari data telemetri fisik murni (*unclamped*) yang direkam oleh 3 node ESP32 di TimescaleDB.
3. **Hyperparameter Tuning & Optimasi Model** untuk memaksimalkan *F1-Score* dan meminimalkan *False Alarm Rate* ($FAR < 0.1\%$).
4. **Porting dan Kompilasi C/C++ ke ESP32**: Memastikan model dapat berjalan dalam batasan sumber daya mikrokontroler (RAM $< 50\text{ KB}$, Flash $< 100\text{ KB}$, Latensi $< 5\text{ ms}$).
5. **Hardware-in-the-Loop (HIL) Benchmarking**: Mengukur secara empiris akurasi, waktu inferensi, dan konsumsi memori langsung di perangkat keras ESP32.

---

## 🏗️ 1. Fase 1: Data Acquisition, Cleaning & Preparation

### 1.1 Ekstraksi Data dari TimescaleDB
Data ditarik dari tabel `tb_sensor_telemetry` yang mencatat data fisik kontinu pada interval $100\text{ ms}$ ($10\text{ Hz}$):

```sql
SELECT 
    ts,
    node_id,
    pga,
    sta_lta,
    dominant_freq,
    rms,
    ml_prob,
    temp,
    pressure
FROM tb_sensor_telemetry
WHERE ts >= NOW() - INTERVAL '7 days'
ORDER BY ts ASC;
```

### 1.2 Pipeline Data Cleaning
1. **Pembersihan Outlier & Artefak Hardware**:
   - Menghapus nilai `NULL`, `NaN`, atau `inf`.
   - Filter pembacaan I2C glitch yang tidak wajar ($\text{PGA} > 3.0\text{g}$ dengan durasi 1 sampel saja tanpa osilasi sinusoidal).
2. **Normalisasi Noise Floor & Tare**:
   - Memanfaatkan baseline kalibrasi DC tare gravitasi bumi ($0.000\text{ m/s}^2$).
   - Fitur dinamik $a_x, a_y, a_z$ diisolasi dari komponen statis gravitasi $1\text{g}$.
3. **Segmentasi Jendela Waktu (Sliding Window)**:
   - Jendela analisis: $2.0\text{ detik}$ ($20\text{ sampel}$ pada $10\text{ Hz}$).
   - *Stride / Step*: $0.2\text{ detik}$ ($2\text{ sampel}$, overlap $90\%$).

### 1.3 Feature Engineering Matrix (Input Vector $\mathbf{X}$)
Setiap sampel jendela dikonversi menjadi vektor fitur 6-dimensi:

$$\mathbf{X} = \begin{bmatrix} x_{\text{PGA}}, & x_{\text{STA/LTA}}, & x_{f_{\text{dom}}}, & x_{\text{RMS}}, & x_{\Delta t}, & x_{\text{PIR}} \end{bmatrix}$$

- **$x_{\text{PGA}}$**: Peak Ground Acceleration maksimum dalam jendela ($g$).
- **$x_{\text{STA/LTA}}$**: Rasio energi rata-rata pendek ($0.1\text{s}$) terhadap rata-rata panjang ($20\text{s}$). Baseline normal $\approx 1.00$.
- **$x_{f_{\text{dom}}}$**: Frekuensi dominan hasil Zero-Crossing Rate (ZCR) atau FFT ($0 - 50\text{ Hz}$).
- **$x_{\text{RMS}}$**: Root Mean Square akselerasi dinamik 3-sumbu.
- **$x_{\Delta t}$**: Durasi getaran aktif yang berkelanjutan ($\ge 0.008\text{g}$).
- **$x_{\text{PIR}}$**: Status detektor inframerah manusia ($0.0 = \text{kosong}, 1.0 = \text{ada manusia}$), untuk memfilter goncangan meja akibat aktivitas manusia.

### 1.4 Penyeimbangan Kelas (Class Balancing)
Data kondisi tenang (*ambient noise*) jauh lebih mendominasi dibandingkan getaran gempa ($> 98\%$ vs $< 2\%$).
- **Strategi Penyeimbangan**:
  - *Undersampling* data tenang berlebihan.
  - *Data Augmentation*: Menginjeksikan rekaman gempa historis BMKG dan USGS (misal: Gempa Chiba M4.8 dan Cianjur) yang di-resample ke $10\text{ Hz}$.
  - Menggunakan teknik **SMOTE** (*Synthetic Minority Over-sampling Technique*) untuk melatih model klasik.

---

## 🤖 2. Fase 2: Kandidat Model TinyML

Kami membandingkan 5 keluarga arsitektur model:

```
                           ┌───────────────────────────────┐
                           │      Input: Feature Vector    │
                           │   [PGA, STA/LTA, Hz, RMS, t]  │
                           └───────────────┬───────────────┘
                                           │
         ┌──────────────────┬──────────────┼──────────────────┬─────────────────┐
         ▼                  ▼              ▼                  ▼                 ▼
   [Baseline]            [Model 1]     [Model 2]          [Model 3]         [Model 4]
   Heuristik Fisika      Linear &      Random             Multilayer        1D-CNN
   (Allen STA/LTA)       RBF SVM       Forest             Perceptron (ANN)  (Raw Waveform)
         │                  │              │                  │                 │
   Rule Engine          Hyperplane    Decision Tree       TFLite Micro       TFLite Micro
   Sub-microsec         ~0.1 ms       ~0.02 ms            ~1.0 ms            ~8.0 ms
```

### Model 1: Support Vector Machine (SVM)
- **Linear SVM**: Pemisah margin linear sederhana ($w^T x + b = 0$). Sangat ringan.
- **RBF Kernel SVM**: Kernel non-linear $K(x, x') = \exp(-\gamma ||x - x'||^2)$. Ideal untuk memisahkan getaran frekuensi rendah gempa vs getaran frekuensi tinggi benturan meja.
- **Tooling**: `scikit-learn` $\rightarrow$ `micromlgen` $\rightarrow$ C++ Class murni tanpa dependensi.

### Model 2: Random Forest / ExtraTrees Classifier
- **Arsitektur**: Ensembel 10–25 Decision Trees dengan kedalaman maksimum (*max_depth*) 5–8.
- **Keunggulan di Edge**: Dikonversi menjadi nested `if-else` murni dalam C. Menggunakan $0\text{ bytes}$ RAM dinamis.
- **Tooling**: `scikit-learn` $\rightarrow$ `emlearn` / `m2cgen` $\rightarrow$ `lindu_rf_model.h`.

### Model 3: Multilayer Perceptron (MLP / ANN)
- **Arsitektur**: `Input(6) -> Dense(16, ReLU) -> Dense(8, ReLU) -> Dense(1, Sigmoid)`.
- **Keunggulan**: Menghasilkan probabilitas kontinu ($0.0\% - 100.0\%$) yang sangat mulus untuk *shadow mode*.
- **Tooling**: `TensorFlow/Keras` $\rightarrow$ Post-Training Int8 Quantization $\rightarrow$ `TensorFlow Lite for Microcontrollers (TFLM)`.

### Model 4: 1D-Convolutional Neural Network (1D-CNN Waveform)
- **Arsitektur**: `Conv1D(8, kernel=3) -> MaxPool -> Conv1D(16, kernel=3) -> GlobalAvgPool -> Dense(1, Sigmoid)`.
- **Input**: Raw 3-axis acceleration array $[20 \times 3]$ ($2\text{ detik}$ sinyal).
- **Keunggulan**: Menganalisis *signature* gelombang P (*Primary Wave*) sebelum fase gelombang S yang merusak tiba.

### Model 5: Logistic Regression (Baseline Matematis)
- **Persamaan**: $P = \frac{1}{1 + e^{-(\beta_0 + \sum \beta_i x_i)}}$.
- **Keunggulan**: Standar kalibrasi minimum untuk membuktikan signifikansi performa model yang lebih kompleks.

---

## ⚙️ 3. Fase 3: Training, Hyperparameter Tuning & Analisa

### 3.1 Skema Validasi Silang (Cross-Validation)
- **Metode**: *Stratified 5-Fold Cross Validation* dengan pembagian berbasis waktu (*Time-Series Group K-Fold*) untuk mencegah kebocoran data (*data leakage* temporal).
- **Partisi Data**:
  - $70\%$ Training Set.
  - $15\%$ Validation Set (tuning threshold).
  - $15\%$ Holdout Test Set (evaluasi akhir).

### 3.2 Hyperparameter Tuning Space
Tuning dilakukan menggunakan pustaka **`Optuna`** atau **`GridSearchCV`**:

| Model | Hyperparameter yang Di-tuning | Rentang Eksplorasi |
| :--- | :--- | :--- |
| **SVM** | $C$ (Regularisasi)<br>$\gamma$ (Kernel Coefficient)<br>Kernel Type | $10^{-2} \le C \le 10^3$<br>$10^{-4} \le \gamma \le 10^1$<br>`['linear', 'rbf', 'poly']` |
| **Random Forest** | `n_estimators`<br>`max_depth`<br>`min_samples_split` | $10 \le n \le 50$<br>$3 \le d \le 10$<br>$2 \le s \le 10$ |
| **MLP (ANN)** | Hidden units<br>Learning rate ($\eta$)<br>Weight decay ($L_2$) | $[8, 16, 32]$ units<br>$10^{-4} \le \eta \le 10^{-2}$<br>$10^{-5} \le L_2 \le 10^{-2}$ |
| **1D-CNN** | Kernel size<br>Filter count<br>Dropout rate | $k \in [3, 5]$<br>filters $\in [8, 16, 32]$<br>$0.1 \le \text{dropout} \le 0.4$ |

### 3.3 Metrik Evaluasi Komprehensif
Sistem Peringatan Dini Gempa memiliki persyaratan unik: **False Alarm Rate (FAR) harus sekecil mungkin**, sementara **Recall pada gempa nyata harus mendekati $100\%$**:

1. **Recall / Sensitivity ($TPR$)**: $\frac{TP}{TP + FN}$ (Target: $\ge 98.0\%$).
2. **False Alarm Rate ($FPR$)**: $\frac{FP}{FP + TN}$ (Target: $< 0.1\%$).
3. **Precision**: $\frac{TP}{TP + FP}$ (Target: $\ge 95.0\%$).
4. **F1-Score / F2-Score**: Memberi bobot lebih tinggi pada Recall ($F_2$).
5. **ROC-AUC & PR-AUC Curve**: Menilai stabilitas model pada berbagai threshold ambang deteksi.

---

## 💻 4. Fase 4: Porting & Integrasi Firmware ESP32

### 4.1 Pipeline Konversi Model ke Header C++
Setiap model yang berhasil dilatih akan di-generate menjadi header C/C++ mandiri:

1. **Untuk SVM (`micromlgen`)**:
   ```bash
   python -c "from micromlgen import port; print(port(best_svm))" > lindu_node/include/svm_model.h
   ```
2. **Untuk Random Forest (`emlearn`)**:
   ```bash
   python -c "import emlearn; emlearn.convert(best_rf).save(file='lindu_node/include/rf_model.h')"
   ```
3. **Untuk Neural Network / TFLite Micro**:
   ```bash
   xxd -i lindu_ann_quantized.tflite > lindu_node/include/tflite_model_data.h
   ```

### 4.2 Integrasi Arsitektur Dual-Track di `SensorManager.cpp`
Firmware ESP32 menjalankan model terpilih secara paralel dalam *Shadow Mode* sebelum diaktifkan ke relay aktuator:

```cpp
// TRACK 1: Heuristik Fisika Seismik BMKG (Allen STA/LTA)
bool is_physical_trigger = (pga >= 0.0080f && current_hz <= 15 && sta_lta >= 1.50f);

// TRACK 2: TinyML Edge Inference
float ml_features[6] = {pga, sta_lta, current_hz, rms, duration_s, pir_state};
float ml_probability = lindu_predict(ml_features);
bool is_ml_trigger = (ml_probability >= 0.50f);

// Kesepakatan (Agreement)
bool ml_agree = (is_physical_trigger == is_ml_trigger);
```

---

## 🔬 5. Fase 5: Hardware-in-the-Loop (HIL) Testing & Benchmarking

Eksperimen empiris langsung pada mikrokontroler ESP32:

### 5.1 Parameter Benchmark ESP32
1. **Waktu Inferensi (*Inference Latency*)**:
   Diukur menggunakan fungsi `micros()` presisi tinggi:
   ```cpp
   uint32_t t_start = micros();
   float prob = lindu_predict(features);
   uint32_t t_latency_us = micros() - t_start;
   ```
2. **Konsumsi Memori RAM (*SRAM Heap*)**:
   Diukur menggunakan `esp_get_free_heap_size()` sebelum dan sesudah alokasi model.
3. **Ukuran Biner Flash (*Program Storage Space*)**:
   Diukur melalui output build PlatformIO (`.bin` size delta).
4. **Konsumsi Daya & Suhu Chip**:
   Mengamati apakah inferensi pada loop $10\text{ Hz}$ meningkatkan suhu prosesor (`temperatureRead()`).

### 5.2 Format Tabel Hasil Pengujian (Target Pelaporan Paper/Tesis)

| Model | Ukuran Model (Flash) | Konsumsi RAM | Latensi Inferensi | Akurasi F1-Score | False Alarm Rate | Kesimpulan Kelayakan ESP32 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Heuristik Fisika** | $< 1 \text{ KB}$ | $0 \text{ KB}$ | $< 0.01 \text{ ms}$ | $96.5\%$ | $0.20\%$ | Baseline standar |
| **Linear SVM** | $\sim 2 \text{ KB}$ | $0 \text{ KB}$ | $\sim 0.04 \text{ ms}$ | $97.8\%$ | $0.08\%$ | Sangat layak & ultra-cepat |
| **RBF SVM** | $\sim 15 \text{ KB}$ | $< 1 \text{ KB}$ | $\sim 0.35 \text{ ms}$ | $99.1\%$ | $0.03\%$ | **Rekomendasi Utama Edge** |
| **Random Forest** | $\sim 8 \text{ KB}$ | $0 \text{ KB}$ | $\sim 0.02 \text{ ms}$ | $98.9\%$ | $0.04\%$ | **Rekomendasi Utama Edge** |
| **MLP (ANN 2-layer)** | $\sim 35 \text{ KB}$ | $8 \text{ KB}$ | $\sim 1.20 \text{ ms}$ | $99.2\%$ | $0.02\%$ | Layak via TFLM |
| **1D-CNN** | $\sim 75 \text{ KB}$ | $28 \text{ KB}$ | $\sim 8.50 \text{ ms}$ | $99.4\%$ | $0.01\%$ | Berat di ESP32, batas atas 10Hz |

---

## 📊 6. Fase 6: Visualisasi & Monitoring Live di Grafana

Setelah model di-deploy ke armada node, Grafana memantau metrik performa secara transparan:
1. **Panel Evaluasi Akurasi (Panel 28)**: Menghitung secara real-time persentase kesepakatan (*agreement rate*) antara AI dan fisika klasik.
2. **Distribusi Probabilitas (Panel 27)**: Memastikan probabilitas kondisi tenang tetap di rentang $0\% - 5\%$ tanpa adanya *spurious drift*.
3. **Confusion Matrix Live**: Menghitung True Positive ($TP$), False Positive ($FP$), True Negative ($TN$), dan False Negative ($FN$) berdasarkan validasi silang konsensus multi-node.

---

## 🗓️ 7. Roadmap Pelaksanaan Step-by-Step

```
[Minggu 1: Data Preparation]
  ├── Ekspor data 7 hari terakhir dari TimescaleDB ke CSV/Parquet
  ├── Cleaning outlier & pelabelan ground truth (Tenang vs Getaran Buatan vs Gempa)
  └── Pembagian train/val/test splits

[Minggu 2: Training & Tuning Model Klasik]
  ├── Training Logistic Regression, SVM (Linear & RBF), Random Forest di Python
  ├── Hyperparameter tuning dengan Optuna (F2-score optimization)
  └── Evaluasi Confusion Matrix & PR-AUC di Jupyter/Script

[Minggu 3: Training Deep Learning TinyML]
  ├── Training MLP dan 1D-CNN di TensorFlow/Keras
  ├── Post-training Int8 Quantization
  └── Validasi akurasi loss pasca-kuantisasi

[Minggu 4: Porting C++ & Benchmarking ESP32]
  ├── Generate header C++ (micromlgen, emlearn, TFLM)
  ├── Build firmware & ukur Flash/RAM footprint
  ├── Deploy OTA ke 3 Node Lindu
  └── Uji HIL dengan getaran nyata & catat waktu komputasi mikrodetik

[Minggu 5: Dokumentasi & Pelaporan Tesis]
  ├── Rekapitulasi tabel perbandingan akurasi vs latensi
  └── Penyusunan bab hasil dan pembahasan di naskah ilmiah
```
