"""
Basic Module for Smart Executor - العمليات الأساسية
"""

import hashlib
import json
from datetime import datetime


class BasicCryptoModule:
    """العمليات التشفيرية الأساسية"""
    
    def __init__(self):
        self.name = "BasicCryptoModule"
        self.version = "2.0"
    
    def calculate_hash(self, data: str) -> str:
        """حساب هاش SHA-256"""
        return hashlib.sha256(data.encode()).hexdigest()
    
    def verify_integrity(self, data: str, expected_hash: str) -> bool:
        """التحقق من سلامة البيانات"""
        return self.calculate_hash(data) == expected_hash
    
    def timestamp_data(self, data: dict) -> dict:
        """إضافة طابع زمني وتوقيع"""
        timestamped = data.copy()
        timestamped['timestamp'] = datetime.now().isoformat()
        timestamped['integrity_hash'] = self.calculate_hash(
            json.dumps(timestamped, sort_keys=True)
        )
        return timestamped
    
    def process_from_c(self, c_data: dict) -> dict:
        """معالجة البيانات من Module C"""
        print(f"🔗 {self.name}: تلقي بيانات من Module C")
        
        # التحقق الأساسي
        if 'summary' not in c_data:
            return {"error": "بيانات C غير صالحة"}
        
        return self.timestamp_data(c_data)
