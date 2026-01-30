import sys
sys.path.insert(0, '/storage/emulated/0/Download/BioShield-Integration')

from src.modules.pathogen_intel.core.cascade_interface import CascadeInterfaceC

interface = CascadeInterfaceC()

# سيناريوهات واقعية
scenarios = [
    ("1. طبيعي", {"water_svi": 0.370, "immunity": 0.739}, "MONITOR_CLOSELY"),
    ("2. خطر واحد", {"water_svi": 0.850, "immunity": 0.739}, "PRE_EMERGENCY_MONITOR"),
    ("3. خطران", {"water_svi": 0.850, "immunity": 0.450}, "CRITICAL_INTERVENTION"),
    ("4. خطر خارجي", {"water_svi": 0.370, "immunity": 0.739, "external_signal": True}, "PRE_EMERGENCY_MONITOR"),
    ("5. كل المخاطر", {"water_svi": 0.900, "immunity": 0.400, "external_signal": True}, "CRITICAL_INTERVENTION"),
]

print("🧪 اختبار منطق v2.1.1")
print("=" * 60)

for name, data, expected in scenarios:
    result = interface.process(data)
    status = "✅" if result['decision'] == expected else "❌"
    print(f"{status} {name}")
    print(f"   البيانات: SVI={data.get('water_svi')}, Immunity={data.get('immunity')}")
    print(f"   المتوقع: {expected}")
    print(f"   النتيجة: {result['decision']}")
    print(f"   external_flag: {result['external_flag']}")
    print()
