#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import json
from datetime import datetime
from adaptive.adaptive_memory import AdaptiveMemory

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

def run_test():
    memory = AdaptiveMemory(component_name="termux_test")

    # محاكاة بيانات دورات اختبارية
    test_cycles = [
        {'svi':0.38, 'quality':62, 'contamination':20, 'status':'GOOD'},
        {'svi':0.40, 'quality':58, 'contamination':25, 'status':'GOOD'},
        {'svi':0.36, 'quality':65, 'contamination':22, 'status':'EXCELLENT'}
    ]

    for i, data in enumerate(test_cycles, 1):
        outcome = {'success': True, 'actual_damage': 25}
        memory.record_cycle(data, action_taken=f"Cycle {i} action", outcome=outcome)

    # تصدير التقرير
    report = memory.export_report()
    report_date = datetime.now().strftime("%Y-%m-%d")
    formatter = ReportFormatter()
    formatter.save_daily_report(report, report_date)

if __name__ == "__main__":
    run_test()
