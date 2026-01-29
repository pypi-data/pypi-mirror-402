#!/usr/bin/env python3
"""
Adaptive Enhancements Module
- Temporal Drift
- Stress Accumulation
- Decision Confidence Regulator
- Early Warning Flag
"""

from collections import deque

class AdaptiveEnhancements:
    def __init__(self, history_length=5, stress_decay=0.9, confidence_window=3, drift_threshold=0.05, stress_threshold=1.5):
        self.svi_history = deque(maxlen=history_length)
        self.stress_accumulator = 0.0
        self.stress_decay = stress_decay
        self.confidence_window = deque(maxlen=confidence_window)
        self.drift_threshold = drift_threshold
        self.stress_threshold = stress_threshold
        self.early_warning = False

    def compute_temporal_drift(self, current_svi):
        if self.svi_history:
            drift = abs(current_svi - self.svi_history[-1])
        else:
            drift = 0.0
        self.svi_history.append(current_svi)
        self.early_warning = drift > self.drift_threshold
        return drift

    def accumulate_stress(self, stress_value):
        # Decay previous stress
        self.stress_accumulator *= self.stress_decay
        self.stress_accumulator += stress_value
        if self.stress_accumulator > self.stress_threshold:
            self.early_warning = True
        return self.stress_accumulator

    def regulate_confidence(self, confidence):
        self.confidence_window.append(confidence)
        avg_conf = sum(self.confidence_window) / len(self.confidence_window)
        # Trigger caution if confidence too low
        caution_flag = avg_conf < 0.5
        if caution_flag:
            self.early_warning = True
        return caution_flag

    def get_early_warning(self):
        return self.early_warning
