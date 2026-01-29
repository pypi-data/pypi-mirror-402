"""
BioShield Orchestrator Module
إدارة وتنسيق تدفق البيانات بين وحدات BioShield
"""

__version__ = "3.0.0"
__author__ = "BioShield Integration Team"
__description__ = "Orchestrates A → AB → B → Adaptive cascade"

from .cascade_manager import CascadeManager
from .data_router import DataRouter

__all__ = ['CascadeManager', 'DataRouter']

print(f"✅ BioShield Orchestrator v{__version__} loaded")
