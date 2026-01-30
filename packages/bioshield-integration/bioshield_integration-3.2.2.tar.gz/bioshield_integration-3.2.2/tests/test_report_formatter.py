#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import json
from datetime import datetime

class ReportFormatter:
    """حفظ التقرير اليومي بشكل مرتب"""
    def save_daily_report(self, report, report_date):
        path = os.path.join("reports", "daily")
        os.makedirs(path, exist_ok=True)
        filename = os.path.join(path, f"report_{report_date}.txt")
        with open(filename, "w", encoding="utf-8") as f:
            f.write("Daily Report Summary\n")
            f.write("="*60 + "\n")
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"✅ Report saved in {filename}")

# مثال اختبار
if __name__ == "__main__":
    sample_report = {
        "summary": {
            "total_cycles": 5,
            "soil_health": "EXCELLENT",
            "average_ph": 6.2,
            "average_moisture": 55,
            "average_temperature": 23
        },
        "recommendations": [
            "مستوى pH مثالي (6.2)",
            "مستوى رطوبة مثالي (55%)",
            "درجة حرارة مثالية (23°C)"
        ]
    }
    report_date = datetime.now().strftime("%Y-%m-%d")
    formatter = ReportFormatter()
    formatter.save_daily_report(sample_report, report_date)
