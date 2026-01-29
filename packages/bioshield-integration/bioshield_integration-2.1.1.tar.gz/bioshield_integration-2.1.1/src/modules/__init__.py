"""
BioShield Integration Modules
Wrappers for A, AB, B, C, D levels
"""

__version__ = "1.0.0"

# Import wrappers when available
try:
    from .hydronet.hydronet_wrapper import HydroNetWrapper
except ImportError:
    HydroNetWrapper = None

try:
    from .aquacrop.aquacrop_wrapper import AquaCropWrapper
except ImportError:
    AquaCropWrapper = None

try:
    from .agro_immunity.agro_immunity_wrapper import AgroImmunityWrapper
except ImportError:
    AgroImmunityWrapper = None

__all__ = [
    'HydroNetWrapper',
    'AquaCropWrapper',
    'AgroImmunityWrapper'
]
