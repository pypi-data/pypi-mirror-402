"""
HydroNet Module - Water intelligence for BioShield
"""

from .basic_module import get_water_metrics

# Import the wrapper - don't catch ImportError, let it fail if missing
from .hydronet_wrapper import HydroNetWrapper, get_hydronet_data

__all__ = ['get_water_metrics', 'HydroNetWrapper', 'get_hydronet_data']
