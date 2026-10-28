#!/usr/bin/env python3
"""
=============================================================================
LINDU MULTICLASS VIBRATION CLASSIFIER - TRAINING & EXPORT ENGINE
=============================================================================
Melatih model TinyML untuk mengklasifikasikan getaran ke dalam 7 kategori fisik:
 0. GEMPA_BUMI       (Real Tectonic Earthquake: M3.0 - M7.8, low-freq 1-8Hz, long duration)
 1. HENTAKAN_PUKULAN (Desk/Table Knock & Punch: high peak, ultra-short, sharp crest)
 2. BENDA_JATUH      (Dropped Object Impact: high freq >40Hz, duration <0.4s)
 3. LANGKAH_KAKI     (Footstep & Stomp: vertical axis dominant, high freq 20-35Hz)
 4. PINTU_BANTING    (Door Slam Shock: structural resonance 30-50Hz, fast decay)
 5. KENDARAAN_LEWAT  (Passing Truck/Traffic: 15-30Hz continuous vibration)
 6. AMBIENT_TENANG   (Quiet Baseline: PGA < 0.008g, sensor thermal noise)
=============================================================================
"""

import csv
import json
import math
import os
import random

SEED = 42
random.seed(SEED)

DATASET_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILE = os.path.join(DATASET_DIR, "realistic_earthquake_and_disturbances_10000.csv")
MODEL_JSON = os.path.join(DATASET_DIR, "multiclass_model_weights.json")
HEADER_FILE = os.path.join(DATASET_DIR, "lindu_multiclass_model.h")

CLASSES = [
    "GEMPA_BUMI",
    "HENTAKAN_PUKULAN",
    "BENDA_JATUH",
    "LANGKAH_KAKI",
    "PINTU_BANTING",
    "KENDARAAN_LEWAT",
    "AMBIENT_TENANG"
]

CLASS_MAP = {
    "earthquake": 0,
    "manual_shake": 1,
    "dropped_object": 2,
    "stomp": 3,
    "door_slam": 4,
    "passing_truck": 5,
    "ambient_noise": 6
}

# 6 Karakteristik Fisik Domain Waktu & Frekuensi
FEATURE_NAMES = [
    "pga",           # Peak Ground Acceleration (g)
    "sta_lta",       # Rasio STA/LTA seismik
    "freq_hz",       # Frekuensi dominan (Hz)
    "rms",           # Root Mean Square energy (g)
    "crest_factor",  # Ketajaman hentakan = pga / (rms + 1e-6)
    "duration_s"     # Durasi getaran (detik)
]

def load_data(csv_path):
    dataset = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cat = row["event_category"]
            if cat not in CLASS_MAP:
                continue
            
            pga = float(row["pga"])
            sta_lta = float(row["sta_lta"])
            freq = float(row["freq_hz"])
            rms = float(row["rms"])
            dur = float(row["duration_s"])
            crest = pga / (rms + 1e-6)
            
            features = [pga, sta_lta, freq, rms, crest, dur]
            label = CLASS_MAP[cat]
            dataset.append((features, label, cat))
    return dataset

# =============================================================================
# DECISION TREE CLASSIFIER (Zero-Dependency, 100% C++ Exportable)
# =============================================================================
class DecisionNode:
    def __init__(self, feature_idx=None, threshold=None, left=None, right=None, probs=None, predicted_class=None):
        self.feature_idx = feature_idx
        self.threshold = threshold
        self.left = left
        self.right = right
        self.probs = probs
        self.predicted_class = predicted_class

    def is_leaf(self):
        return self.predicted_class is not None

def gini_impurity(labels, num_classes):
    if not labels:
        return 0.0
    total = len(labels)
    counts = [0] * num_classes
    for l in labels:
        counts[l] += 1
    return 1.0 - sum((c / total) ** 2 for c in counts)

def build_tree(X, y, depth=0, max_depth=6, min_samples=20, num_classes=7):
    if len(y) <= min_samples or depth >= max_depth or len(set(y)) == 1:
        counts = [0] * num_classes
        for l in y:
            counts[l] += 1
        total = len(y)
        probs = [round(c / total, 4) for c in counts]
        pred_class = counts.index(max(counts))
        return DecisionNode(probs=probs, predicted_class=pred_class)

    best_gini = 1.0
    best_feat = None
    best_thresh = None
    best_left = None
    best_right = None

    n_features = len(X[0])
    current_gini = gini_impurity(y, num_classes)

    for f_idx in range(n_features):
        vals = sorted(list(set(row[f_idx] for row in X)))
        # Uji beberapa kandidat threshold persentil untuk efisiensi
        if len(vals) > 25:
            step = len(vals) // 25
            test_thresholds = [vals[i] for i in range(1, len(vals) - 1, step)]
        else:
            test_thresholds = [(vals[i] + vals[i+1]) / 2.0 for i in range(len(vals) - 1)]

        for thresh in test_thresholds:
            left_idx = [i for i, row in enumerate(X) if row[f_idx] <= thresh]
            right_idx = [i for i, row in enumerate(X) if row[f_idx] > thresh]

            if len(left_idx) < 5 or len(right_idx) < 5:
                continue

            left_y = [y[i] for i in left_idx]
            right_y = [y[i] for i in right_idx]

            g = (len(left_y) * gini_impurity(left_y, num_classes) + 
                 len(right_y) * gini_impurity(right_y, num_classes)) / len(y)

            if g < best_gini:
                best_gini = g
                best_feat = f_idx
                best_thresh = thresh
                best_left = (left_idx, left_y)
                best_right = (right_idx, right_y)

    if best_feat is None or (current_gini - best_gini) < 0.001:
        counts = [0] * num_classes
        for l in y:
            counts[l] += 1
        total = len(y)
        probs = [round(c / total, 4) for c in counts]
        pred_class = counts.index(max(counts))
        return DecisionNode(probs=probs, predicted_class=pred_class)

    left_X = [X[i] for i in best_left[0]]
    right_X = [X[i] for i in best_right[0]]

    left_node = build_tree(left_X, best_left[1], depth + 1, max_depth, min_samples, num_classes)
    right_node = build_tree(right_X, best_right[1], depth + 1, max_depth, min_samples, num_classes)

    return DecisionNode(feature_idx=best_feat, threshold=best_thresh, left=left_node, right=right_node)

def predict_single(node, x):
    curr = node
    while not curr.is_leaf():
        if x[curr.feature_idx] <= curr.threshold:
            curr = curr.left
        else:
            curr = curr.right
    return curr.predicted_class, curr.probs

def export_tree_to_cpp(node, indent="    "):
    if node.is_leaf():
        probs_str = ", ".join(f"{p:.3f}f" for p in node.probs)
        return (f"{indent}result.predicted_class = {node.predicted_class};\n"
                f"{indent}result.class_name = VIBRATION_CLASSES[{node.predicted_class}];\n"
                f"{indent}static const float p[{len(node.probs)}] = {{{probs_str}}};\n"
                f"{indent}memcpy(result.confidence, p, sizeof(p));\n"
                f"{indent}return result;\n")

    feat_name = FEATURE_NAMES[node.feature_idx]
    cond = f"{feat_name} <= {node.threshold:.6f}f"
    
    code = f"{indent}if ({cond}) {{\n"
    code += export_tree_to_cpp(node.left, indent + "    ")
    code += f"{indent}}} else {{\n"
    code += export_tree_to_cpp(node.right, indent + "    ")
    code += f"{indent}}}\n"
    return code

def main():
    print("=" * 70)
    print("  🚀 LINDU MULTICLASS VIBRATION CLASSIFIER TRAINING")
    print("=" * 70)

    dataset = load_data(CSV_FILE)
    print(f"[*] Dataset terbaca: {len(dataset):,} sampel dari 7 kategori fisik")

    random.shuffle(dataset)
    split = int(len(dataset) * 0.80)
    train_data = dataset[:split]
    test_data = dataset[split:]

    X_train = [x[0] for x in train_data]
    y_train = [x[1] for x in train_data]
    X_test = [x[0] for x in test_data]
    y_test = [x[1] for x in test_data]

    print(f"[*] Data Train: {len(X_train):,} sampel | Data Test: {len(X_test):,} sampel")
    print("[*] Melatih Decision Tree TinyML (Depth=6)...")

    root = build_tree(X_train, y_train, depth=0, max_depth=6, min_samples=25, num_classes=len(CLASSES))

    # Evaluasi pada data uji (Test Set)
    correct = 0
    confusion_matrix = [[0] * len(CLASSES) for _ in range(len(CLASSES))]

    for x, y_true in zip(X_test, y_test):
        pred_cls, _ = predict_single(root, x)
        confusion_matrix[y_true][pred_cls] += 1
        if pred_cls == y_true:
            correct += 1

    accuracy = (correct / len(y_test)) * 100.0
    print(f"\n[+] Akurasi Evaluasi Test Set: {accuracy:.2f}%\n")

    print(f"{'Kategori Sebenarnya':<20} | {'Sampel':<8} | {'Precision':<10} | {'Recall':<10} | {'F1-Score':<10}")
    print("-" * 68)
    for c_idx, c_name in enumerate(CLASSES):
        total_actual = sum(confusion_matrix[c_idx])
        tp = confusion_matrix[c_idx][c_idx]
        total_pred = sum(confusion_matrix[i][c_idx] for i in range(len(CLASSES)))
        
        prec = (tp / total_pred * 100.0) if total_pred > 0 else 0.0
        rec = (tp / total_actual * 100.0) if total_actual > 0 else 0.0
        f1 = (2 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0

        print(f"{c_name:<20} | {total_actual:<8} | {prec:<9.1f}% | {rec:<9.1f}% | {f1:<9.1f}%")

    # Generate C++ Header untuk ESP32
    cpp_code = f"""/**
 * LINDU-EEW: TinyML Multiclass Vibration Classifier for ESP32
 * Auto-generated by train_multiclass_vibration_model.py
 *
 * Classes:
 *  0: GEMPA_BUMI
 *  1: HENTAKAN_PUKULAN
 *  2: BENDA_JATUH
 *  3: LANGKAH_KAKI
 *  4: PINTU_BANTING
 *  5: KENDARAAN_LEWAT
 *  6: AMBIENT_TENANG
 */

#ifndef LINDU_MULTICLASS_MODEL_H
#define LINDU_MULTICLASS_MODEL_H

#include <Arduino.h>

static const char* VIBRATION_CLASSES[7] = {{
    "GEMPA_BUMI",
    "HENTAKAN_PUKULAN",
    "BENDA_JATUH",
    "LANGKAH_KAKI",
    "PINTU_BANTING",
    "KENDARAAN_LEWAT",
    "AMBIENT_TENANG"
}};

struct VibrationClassification {{
    int predicted_class;
    const char* class_name;
    float confidence[7];
}};

inline VibrationClassification classify_vibration(float pga, float sta_lta, float freq_hz, float rms, float duration_s) {{
    VibrationClassification result;
    
    // Quiet Baseline Gate (< 0.0080g = 100% AMBIENT TENANG)
    if (pga < 0.0080f) {{
        result.predicted_class = 6;
        result.class_name = VIBRATION_CLASSES[6];
        for (int i = 0; i < 7; i++) result.confidence[i] = 0.0f;
        result.confidence[6] = 0.98f;
        result.confidence[0] = 0.01f;
        return result;
    }}

    float crest_factor = pga / (rms + 1e-6f);

{export_tree_to_cpp(root, "    ")}
}}

#endif // LINDU_MULTICLASS_MODEL_H
"""

    with open(HEADER_FILE, "w", encoding="utf-8") as f:
        f.write(cpp_code)
    print(f"\n[✔] Embedded C++ Header berhasil diekspor ke: {HEADER_FILE}")

if __name__ == "__main__":
    main()
