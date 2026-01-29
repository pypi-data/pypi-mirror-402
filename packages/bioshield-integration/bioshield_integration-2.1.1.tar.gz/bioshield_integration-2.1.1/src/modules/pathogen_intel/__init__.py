"""
Pathogen Intelligence Module v2.1.2
BioShield-Integration - نظام ذكي لتحليل مسببات الأمراض

مميزات v2.1.2:
- منطق قرار منفصل واضح
- عتبات مختلفة للخطر المحلي والخارجي
- عد دقيق لشروط الخطر (CRITICAL يتطلب شرطين على الأقل)
- تفسيرات مفصلة لكل نوع خطر
- ثقة ثابتة 85%
"""

__version__ = "2.1.2"
__stage__ = "C"
__status__ = "Active"
__model_name__ = "BioShield-Pathogen-Intelligence-v2.1.2"

def get_module_info():
    return {
        "module": "pathogen_intel",
        "version": __version__,
        "stage": __stage__,
        "status": __status__,
        "description": "نظام مراقبة مسببات الأمرام مع منطق قرار محسن",
        "features": [
            "منطق_قرار_منفصل",
            "عتبات_مختلفة_محلي_خارجي",
            "ثقة_85%_ثابتة",
            "شرطان_لـ_CRITICAL",
            "تفسيرات_مفصلة"
        ],
        "thresholds": {
            "local_water_svi": 0.8,
            "local_immunity": 0.6,
            "external_water_svi": 0.9,
            "external_immunity": 0.5
        }
    }
