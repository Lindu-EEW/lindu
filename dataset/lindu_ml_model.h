/**
 * Lindu-EEW: On-Device Machine Learning Earthquake Classifier (Auto-Generated)
 * Architecture: Logistic Regression with Feature Standardization
 * Generated on 1,000 Balanced Training Samples
 */

#ifndef LINDU_ML_MODEL_H
#define LINDU_ML_MODEL_H

#include <math.h>

#define ML_NUM_FEATURES 6

// Feature order: pga, sta_lta, freq_hz, rms, duration_s, p_to_s_ratio
static const float ML_MEANS[6] = {0.167650f, 7.604420f, 12.011750f, 0.082071f, 21.913950f, 0.605856f};
static const float ML_STDS[6]  = {0.203223f, 7.320262f, 13.760565f, 0.113894f, 19.507890f, 0.228757f};
static const float ML_WEIGHTS[6] = {-0.262834f, 1.901669f, -3.787374f, 0.832697f, 0.477519f, -2.231301f};
static const float ML_BIAS = 0.175546f;

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
                                             float rms, float duration_s, float p_to_s_ratio) {
    float feats[ML_NUM_FEATURES] = {pga, sta_lta, freq_hz, rms, duration_s, p_to_s_ratio};
    float z = ML_BIAS;
    for (int i = 0; i < ML_NUM_FEATURES; ++i) {
        float normalized = (feats[i] - ML_MEANS[i]) / ML_STDS[i];
        z += ML_WEIGHTS[i] * normalized;
    }
    if (z < -20.0f) return 0.0f;
    if (z > 20.0f) return 1.0f;
    return 1.0f / (1.0f + expf(-z));
}

#endif // LINDU_ML_MODEL_H
