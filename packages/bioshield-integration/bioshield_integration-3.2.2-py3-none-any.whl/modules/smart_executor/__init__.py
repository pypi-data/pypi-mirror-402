"""
smart_executor module for BioShield-Integration
Smart Decision Execution with Feedback Loop
"""

__version__ = "3.1.0"
__author__ = "BioShield Team"
__description__ = "Module D+ - Smart Executor with 4 Components"

from .smart_executor_wrapper import SmartExecutorDPlus
from .basic_module import BasicCryptoModule

__all__ = ['SmartExecutorDPlus', 'BasicCryptoModule']
