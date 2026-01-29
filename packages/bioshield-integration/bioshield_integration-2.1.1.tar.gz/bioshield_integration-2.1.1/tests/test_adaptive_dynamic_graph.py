#!/usr/bin/env python3
"""
Dynamic Graph Test for AdaptiveEngine
Plots StressBurden, Drift, and InterventionScore per cycle
Saves each cycle as PNG (Termux compatible)
"""

import sys
import os
import time
from random import uniform

# --- Ensure adaptive/ folder is in the path ---
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'adaptive'))

from adaptive_engine import AdaptiveEngine

# --- Matplotlib non-interactive backend for Termux ---
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

engine = AdaptiveEngine(component_name="dynamic_graph")

# Data containers
cycles = []
stress_burden_list = []
drift_list = []
intervention_score_list = []

print("🚀 Starting dynamic graph test...")

for cycle in range(1, 11):
    water_data = {'svi': round(uniform(0.2, 0.5), 3),
                  'quality': round(uniform(60, 80), 1),
                  'contamination': round(uniform(10, 30), 1)}
    soil_data = {'bacteria_species':[100, 90, 80],
                 'fungi_species':[50, 40],
                 'nutrients':{'N':40, 'P':30, 'K':42},
                 'pH':6.7,
                 'moisture':55}
    crop_data = {'type':'wheat', 'growth_stage':'flowering'}

    decision = engine.decide_intervention(water_data, soil_data, crop_data)

    cycles.append(cycle)
    stress_burden_list.append(decision['factors']['stress_burden'])
    drift_list.append(decision['factors'].get('drift', 0))
    intervention_score_list.append(decision['factors']['intervention_score'])

    # Plot after each cycle
    plt.figure(figsize=(8,5))
    plt.plot(cycles, stress_burden_list, marker='o', label='Stress Burden')
    plt.plot(cycles, drift_list, marker='x', label='Temporal Drift')
    plt.plot(cycles, intervention_score_list, marker='s', label='Intervention Score')
    plt.xlabel("Cycle")
    plt.ylabel("Value")
    plt.title("Adaptive Engine Dynamics")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()

    img_path = os.path.join(os.path.dirname(__file__), f"cycle_{cycle}.png")
    plt.savefig(img_path)
    plt.close()
    print(f"✅ Cycle {cycle} completed, graph saved to {img_path}")
    time.sleep(1)  # simulate delay

print("🎯 Dynamic graph test completed.")
