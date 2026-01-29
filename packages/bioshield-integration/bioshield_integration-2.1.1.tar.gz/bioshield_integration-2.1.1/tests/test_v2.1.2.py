import sys
sys.path.insert(0, '/storage/emulated/0/Download/BioShield-Integration')

from src.modules.pathogen_intel.core.cascade_interface import CascadeInterfaceC

interface = CascadeInterfaceC()

scenarios = [
    ("1. طبيعي", {"water_svi": 0.370, "immunity": 0.739}, "MONITOR_CLOSELY"),
    ("2. خطر مائي واحد", {"water_svi": 0.850, "immunity": 0.739}, "PRE_EMERGENCY_MONITOR"),
    ("3. خطران (مائي+مناعة)", {"water_svi": 0.850, "immunity": 0.450}, "CRITICAL_INTERVENTION"),
    ("4. خطر خارجي فقط", {"water_svi": 0.370, "immunity": 0.739, "external_signal": True}, "PRE_EMERGENCY_MONITOR"),
    ("5. كل المخاطر", {"water_svi": 0.900, "immunity": 0.400, "external_signal": True}, "CRITICAL_INTERVENTION"),
]

print("🧪 اختبار v2.1.2 - منطق منفصل")
print("=" * 60)

for name, data, expected in scenarios:
    print(f"\n{name}")
    print(f"   البيانات: SVI={data.get('water_svi')}, Immunity={data.get('immunity')}")
    result = interface.process(data)
    status = "✅" if result['decision'] == expected else "❌"
    print(f"   {status} المتوقع: {expected}")
    print(f"      النتيجة: {result['decision']}")
    print(f"      شروط الخطر: {result['critical_conditions']}")
    print(f"      external_flag: {result['external_flag']}")
