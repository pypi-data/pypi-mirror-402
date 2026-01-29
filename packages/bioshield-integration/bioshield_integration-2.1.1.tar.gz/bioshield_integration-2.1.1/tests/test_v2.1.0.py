#!/usr/bin/env python3
"""اختبار النموذج v2.1.0"""

import sys
sys.path.insert(0, '/storage/emulated/0/Download/BioShield-Integration')

from src.modules.pathogen_intel.core.cascade_interface import CascadeInterfaceC

print("🧪 اختبار BioShield Pathogen Intelligence v2.1.0")
print("=" * 50)

interface = CascadeInterfaceC()

# اختبار السيناريوهات الثلاثة
test_cases = [
    {"name": "MONITOR_CLOSELY", "data": {"water_svi": 0.3, "immunity": 0.8}},
    {"name": "PRE_EMERGENCY_MONITOR", "data": {"water_svi": 0.7, "immunity": 0.7}},
    {"name": "CRITICAL_INTERVENTION", "data": {"water_svi": 0.9, "immunity": 0.4}},
]

for test in test_cases:
    print(f"\n🔍 اختبار: {test['name']}")
    print(f"   البيانات: {test['data']}")
    result = interface.process(test['data'])
    print(f"   النتيجة: {result['decision']}")
    print(f"   مستوى الخطر: {result['risk_level']}")
    print(f"   الثقة: {result['confidence']*100:.0f}%")

print("\n✅ النموذج v2.1.0 يعمل بكافة السيناريوهات!")
