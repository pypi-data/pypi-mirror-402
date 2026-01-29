#!/usr/bin/env python3
"""
Basic implementation for aquacrop module
"""

class AquacropBasic:
    """Basic implementation"""
    def __init__(self):
        self.version = "1.0.0"
        self.active = True
    
    def get_status(self):
        return {"module": "aquacrop", "status": "active", "version": self.version}
