#!/usr/bin/env python3
import requests
import json
from datetime import datetime

def test_webhook():
    """اختبار إرسال إلى Pipedream"""
    url = "https://eoi3vhd0zol7y5o.m.pipedream.net"
    
    data = {
        "timestamp": datetime.now().isoformat(),
        "alert_type": "CRITICAL",
        "water_svi": 1.0,
        "immunity_score": 0.7,
        "confidence": 0.85,
        "message": "🚨 TEST from BioShield",
        "system": "BioShield Cascade",
        "alert_id": f"TEST-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    }
    
    print(f"📤 Sending test to: {url}")
    print(f"📦 Data: {json.dumps(data, indent=2)}")
    
    try:
        response = requests.post(url, json=data, timeout=10)
        print(f"✅ Response: {response.status_code}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_webhook()
