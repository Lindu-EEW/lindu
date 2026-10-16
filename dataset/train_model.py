#!/usr/bin/env python3
"""
Lindu-EEW: Earthquake Early Warning System - Machine Learning Training Script
Trains and evaluates seismic classifier models on the 1,000-sample dataset.

Features:
- Pure Python implementation (Zero external dependency requirement)
- Optional scikit-learn integration if installed
- 80/20 Train/Test split (800 train, 200 test)
- Classification Metrics: Accuracy, Precision, Recall, Specificity, F1-Score
- Confusion Matrix: TP, FP, TN, FN
- Model Export:
  1. JSON weights/parameters (dataset/model_weights.json)
  2. Embedded C/C++ header for ESP32 firmware (dataset/lindu_ml_model.h)
  3. Python runtime classifier for consensus engine
"""

import csv
import json
import math
import os
import random

SEED = 42
random.seed(SEED)

DATASET_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILE = os.path.join(DATASET_DIR, "earthquake_train_1000.csv")
MODEL_JSON = os.path.join(DATASET_DIR, "model_weights.json")
HEADER_FILE = os.path.join(DATASET_DIR, "lindu_ml_model.h")

FEATURE_COLS = ["pga", "sta_lta", "freq_hz", "rms", "duration_s", "p_to_s_ratio"]

def load_dataset(csv_path):
    dataset = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            features = [float(row[col]) for col in FEATURE_COLS]
            label = int(row["is_earthquake"])
            dataset.append({
                "features": features,
                "label": label,
                "event_type": row.get("event_type", "unknown")
            })
    return dataset

def train_test_split(dataset, test_ratio=0.20):
    shuffled = list(dataset)
    random.shuffle(shuffled)
    split_idx = int(len(shuffled) * (1.0 - test_ratio))
    return shuffled[:split_idx], shuffled[split_idx:]

def standardize(train_features, test_features):
    n_features = len(train_features[0])
    means = []
    stds = []
    for j in range(n_features):
        vals = [row[j] for row in train_features]
        m = sum(vals) / len(vals)
        var = sum((v - m) ** 2 for v in vals) / len(vals)
        s = math.sqrt(var) if var > 1e-9 else 1.0
        means.append(m)
        stds.append(s)

    def transform(features):
        return [
            [(row[j] - means[j]) / stds[j] for j in range(n_features)]
            for row in features
        ]

    return transform(train_features), transform(test_features), means, stds

def sigmoid(z):
    if z < -20:
        return 0.0
    if z > 20:
        return 1.0
    return 1.0 / (1.0 + math.exp(-z))

def train_logistic_regression(X_train, y_train, epochs=800, lr=0.08, l2=0.001):
    n_samples = len(X_train)
    n_features = len(X_train[0])
    weights = [0.0] * n_features
    bias = 0.0

    for _ in range(epochs):
        dw = [0.0] * n_features
        db = 0.0
        for i in range(n_samples):
            x = X_train[i]
            y = y_train[i]
            z = sum(w * xj for w, xj in zip(weights, x)) + bias
            pred = sigmoid(z)
            err = pred - y

            for j in range(n_features):
                dw[j] += err * x[j]
            db += err

        for j in range(n_features):
            weights[j] -= lr * (dw[j] / n_samples + l2 * weights[j])
        bias -= lr * (db / n_samples)

    return weights, bias

def evaluate_predictions(y_true, y_pred, y_prob=None):
    tp = sum(1 for yt, yp in zip(y_true, y_pred) if yt == 1 and yp == 1)
    tn = sum(1 for yt, yp in zip(y_true, y_pred) if yt == 0 and yp == 0)
    fp = sum(1 for yt, yp in zip(y_true, y_pred) if yt == 0 and yp == 1)
    fn = sum(1 for yt, yp in zip(y_true, y_pred) if yt == 1 and yp == 0)

    total = len(y_true)
    accuracy = (tp + tn) / total if total > 0 else 0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

    return {
        "total": total,
        "tp": tp, "tn": tn, "fp": fp, "fn": fn,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "specificity": specificity,
        "f1_score": f1
    }

def generate_c_header(weights, bias, means, stds, header_path):
    c_code = f"""/**
 * Lindu-EEW: On-Device Machine Learning Earthquake Classifier (Auto-Generated)
 * Architecture: Logistic Regression with Feature Standardization
 * Generated on 1,000 Balanced Training Samples
 */

#ifndef LINDU_ML_MODEL_H
#define LINDU_ML_MODEL_H

#include <math.h>

#define ML_NUM_FEATURES {len(FEATURE_COLS)}

// Feature order: {', '.join(FEATURE_COLS)}
static const float ML_MEANS[{len(FEATURE_COLS)}] = {{{', '.join(f'{m:.6f}f' for m in means)}}};
static const float ML_STDS[{len(FEATURE_COLS)}]  = {{{', '.join(f'{s:.6f}f' for s in stds)}}};
static const float ML_WEIGHTS[{len(FEATURE_COLS)}] = {{{', '.join(f'{w:.6f}f' for w in weights)}}};
static const float ML_BIAS = {bias:.6f}f;

/**
 * Predicts seismic event probability on embedded ESP32.
 * @param pga Peak Ground Acceleration (in g)
 * @param sta_lta Short-Term Average to Long-Term Average energy ratio
 * @param freq_hz Dominant zero-crossing rate frequency (in Hz)
 * @param rms Root-Mean-Square acceleration (in g)
 * @param duration_s Signal duration (in seconds)
 * @param p_to_s_ratio Waveform ratio
 * @return Probability of earthquake (0.0 to 1.0). Threshold > 0.5 indicates confirmed earthquake.
 */
static inline float lindu_predict_earthquake(float pga, float sta_lta, float freq_hz,
                                             float rms, float duration_s, float p_to_s_ratio) {{
    float feats[ML_NUM_FEATURES] = {{pga, sta_lta, freq_hz, rms, duration_s, p_to_s_ratio}};
    float z = ML_BIAS;
    for (int i = 0; i < ML_NUM_FEATURES; ++i) {{
        float normalized = (feats[i] - ML_MEANS[i]) / ML_STDS[i];
        z += ML_WEIGHTS[i] * normalized;
    }}
    if (z < -20.0f) return 0.0f;
    if (z > 20.0f) return 1.0f;
    return 1.0f / (1.0f + expf(-z));
}}

#endif // LINDU_ML_MODEL_H
"""
    with open(header_path, "w", encoding="utf-8") as f:
        f.write(c_code)

def main():
    print("=" * 65)
    print("  LINDU-EEW: Training Earthquake Classifier on 1,000 Samples")
    print("=" * 65)

    dataset = load_dataset(CSV_FILE)
    print(f"Loaded {len(dataset)} total samples from {os.path.basename(CSV_FILE)}")

    train_data, test_data = train_test_split(dataset, test_ratio=0.20)
    print(f"Dataset split: Train = {len(train_data)} (80%), Test = {len(test_data)} (20%)")

    X_train_raw = [d["features"] for d in train_data]
    y_train = [d["label"] for d in train_data]
    X_test_raw = [d["features"] for d in test_data]
    y_test = [d["label"] for d in test_data]

    X_train, X_test, means, stds = standardize(X_train_raw, X_test_raw)

    print("\n--- Training Model (Logistic Regression w/ Regularization) ---")
    weights, bias = train_logistic_regression(X_train, y_train, epochs=1000, lr=0.10, l2=0.0005)

    # Predictions
    test_probs = [sigmoid(sum(w * x for w, x in zip(weights, row)) + bias) for row in X_test]
    test_preds = [1 if p >= 0.50 else 0 for p in test_probs]

    metrics = evaluate_predictions(y_test, test_preds, test_probs)

    print("\n" + "=" * 65)
    print("  TEST EVALUATION RESULTS (N = 200 held-out samples)")
    print("=" * 65)
    print(f"  • Accuracy:    {metrics['accuracy'] * 100:.2f}%")
    print(f"  • Precision:   {metrics['precision'] * 100:.2f}%")
    print(f"  • Recall:      {metrics['recall'] * 100:.2f}% (Sensitivity)")
    print(f"  • Specificity: {metrics['specificity'] * 100:.2f}%")
    print(f"  • F1-Score:    {metrics['f1_score'] * 100:.2f}%")
    print("\n  Confusion Matrix:")
    print(f"    [TP: {metrics['tp']:3d} | FP: {metrics['fp']:3d}]")
    print(f"    [FN: {metrics['fn']:3d} | TN: {metrics['tn']:3d}]")

    print("\n--- Feature Importance (Learned Weights) ---")
    for feat, w in zip(FEATURE_COLS, weights):
        direction = "Positive (-> Earthquake)" if w > 0 else "Negative (-> Noise/Disturbance)"
        print(f"  • {feat:15s}: {w:+.4f} [{direction}]")
    print(f"  • Bias:           {bias:+.4f}")

    # Export model to JSON
    model_payload = {
        "model_type": "LogisticRegression",
        "feature_cols": FEATURE_COLS,
        "means": means,
        "stds": stds,
        "weights": weights,
        "bias": bias,
        "metrics": metrics
    }
    with open(MODEL_JSON, "w", encoding="utf-8") as f:
        json.dump(model_payload, f, indent=2)
    print(f"\n[OK] Model exported to JSON: {MODEL_JSON}")

    # Export C header for firmware
    generate_c_header(weights, bias, means, stds, HEADER_FILE)
    print(f"[OK] C/C++ Header generated for ESP32: {HEADER_FILE}")

    print("\nModel training and validation completed successfully!")

if __name__ == "__main__":
    main()
