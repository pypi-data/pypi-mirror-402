"""
Adaptive Intelligence Module
Transforms B_Agro_Immunity from Constitutive → Adaptive

Three Phases:
1. Adaptive Memory - Learns from past cycles
2. Microbiome Network - Analyzes biological immunity
3. Adaptive Engine - Intelligent decision making

Usage:
    from adaptive import AdaptiveEngine
    
    engine = AdaptiveEngine("my_component")
    decision = engine.decide_intervention(water_data, soil_data, crop_data)
"""

__version__ = "1.0.0"
__author__ = "Samir Baladi - Emerlad Compass"

from .adaptive_memory import AdaptiveMemory
from .microbiome_network import MicrobiomeNetwork
from .adaptive_engine import AdaptiveEngine, GeneticResilience

__all__ = [
    'AdaptiveMemory',
    'MicrobiomeNetwork',
    'AdaptiveEngine',
    'GeneticResilience'
]
