#!/usr/bin/env python3
"""
Dynamic Test for AdaptiveEngine
Runs multiple cycles with simulated water, soil, and crop data
"""

import sys
import os
import time
from random import uniform

# --- إصلاح المسارات ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
src_path = os.path.join(project_root, 'src')

# أضف src إلى المسار إذا لم يكن موجوداً
if src_path not in sys.path:
    sys.path.insert(0, src_path)

print(f"📁 المسار الحالي: {current_dir}")
print(f"📁 جذر المشروع: {project_root}")
print(f"📁 مسار src المضاف: {src_path}")

try:
    from adaptive.adaptive_engine import AdaptiveEngine
    print("✅ تم استيراد AdaptiveEngine بنجاح")
except ImportError as e:
    print(f"❌ فشل الاستيراد: {e}")
    print("📋 محاولة استيراد بديلة...")
    # محاولة استيراد مباشر
    sys.path.insert(0, project_root)
    try:
        from src.adaptive.adaptive_engine import AdaptiveEngine
        print("✅ تم الاستيراد عبر المسار المباشر")
    except ImportError as e2:
        print(f"❌ فشل الاستيراد المباشر: {e2}")
        sys.exit(1)

def generate_water_data():
    return {
        'svi': round(uniform(0.2, 0.5), 3),
        'quality': round(uniform(60, 80), 1),
        'contamination': round(uniform(10, 25), 1)
    }

def generate_soil_data():
    return {
        'bacteria_species': [uniform(50, 120) for _ in range(3)],
        'fungi_species': [uniform(20, 60) for _ in range(2)],
        'nutrients': {'N': uniform(30, 50), 'P': uniform(20, 40), 'K': uniform(35, 50)},
        'pH': round(uniform(6.0, 7.5), 1),
        'moisture': round(uniform(40, 60), 1)
    }

def generate_crop_data():
    return {
        'type': 'wheat',
        'growth_stage': 'flowering'
    }

def run_dynamic_test(cycles=5, interval=2):
    engine = AdaptiveEngine(component_name="dynamic_test")
    print("\n🚀 Starting dynamic test...\n")
    for i in range(cycles):
        print(f"\n=== Cycle #{i+1} ===\n")
        water = generate_water_data()
        soil = generate_soil_data()
        crop = generate_crop_data()
        engine.decide_intervention(water, soil, crop)
        time.sleep(interval)
    print("\n✅ Dynamic test completed\n")

if __name__ == "__main__":
    run_dynamic_test()
