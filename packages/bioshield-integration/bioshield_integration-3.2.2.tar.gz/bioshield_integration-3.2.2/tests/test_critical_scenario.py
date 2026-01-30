#!/usr/bin/env python3
"""
اختبار سيناريو خطر عالي لـ BioShield Integration
يختبر قدرة النظام على توليد CRITICAL_INTERVENTION
"""

import sys
import os

# إضافة مسار المشروع
sys.path.insert(0, '/storage/emulated/0/Download/BioShield-Integration')

def test_critical_scenario():
    """اختبار سيناريو خطر عالي يسبب CRITICAL_INTERVENTION"""
    print("=" * 60)
    print("🧪 اختبار سيناريو CRITICAL_INTERVENTION")
    print("=" * 60)
    
    try:
        # استيراد الوحدة
        from src.modules.pathogen_intel.core.cascade_interface import CascadeInterfaceC
        print("✅ تم استيراد CascadeInterfaceC")
    except ImportError as e:
        print(f"❌ خطأ في الاستيراد: {e}")
        return False
    
    # بيانات تسبب خطراً عالياً
    critical_data = {
        "water_svi": 1.0,        # أقصى خطر
        "immunity": 0.3,         # مناعة منخفضة جداً
        "external_signal": True,
        "immunity_score": 0.3,
        "indicators": {"B1": 0.95, "B2": 0.98, "B3": 0.92},
        "timestamp": "2026-01-19T17:30:00Z"
    }
    
    print(f"\n📊 بيانات الإدخال:")
    print(f"  Water SVI: {critical_data['water_svi']}")
    print(f"  Immunity: {critical_data['immunity']}")
    print(f"  External Signal: {critical_data['external_signal']}")
    
    # تشغيل الاختبار
    interface = CascadeInterfaceC()
    result = interface.receive_from_b(critical_data)
    
    print(f"\n📊 النتائج:")
    print(f"  القرار: {result.get('decision')}")
    print(f"  مستوى الخطر: {result.get('risk_level')}")
    print(f"  درجة الخطر: {result.get('risk_score')}")
    print(f"  الثقة: {result.get('confidence', 0.85)*100:.0f}%")
    print(f"  خطر خارجي: {result.get('external_flag')}")
    
    # التحقق من النتيجة
    if result.get('decision') == 'CRITICAL_INTERVENTION':
        print("\n" + "=" * 60)
        print("✅ ✅ ✅ تم توليد CRITICAL_INTERVENTION بنجاح!")
        print("=" * 60)
        
        # عرض تنبيه كامل
        print("\n" + "=" * 50)
        print("🚨 BioShield CRITICAL Alert")
        print("=" * 50)
        print(f"Alert ID: BS-TEST-CRITICAL")
        print(f"Time: 2026-01-19T17:30:00Z")
        print(f"Alert Type: CRITICAL")
        print(f"System: BioShield Cascade")
        print("-" * 30)
        print("📊 METRICS:")
        print(f"  Water SVI: {critical_data['water_svi']}")
        print(f"  Immunity Score: {critical_data['immunity']}")
        print(f"  Confidence: {result.get('confidence', 0.85)*100:.0f}%")
        print(f"  External Risk: {result.get('external_flag')}")
        print("-" * 30)
        print("💬 MESSAGE:")
        print("  🚨 BioShield Alert: CRITICAL_INTERVENTION required")
        print("=" * 50)
        
        return True
    else:
        print("\n❌ فشل في توليد CRITICAL_INTERVENTION")
        print(f"   سبب: القرار كان {result.get('decision')}")
        return False

def main():
    """الدالة الرئيسية للاختبار"""
    success = test_critical_scenario()
    
    if success:
        print("\n🎉 اختبار CRITICAL_INTERVENTION ناجح!")
        sys.exit(0)
    else:
        print("\n⚠️  اختبار CRITICAL_INTERVENTION فاشل!")
        sys.exit(1)

if __name__ == "__main__":
    main()
