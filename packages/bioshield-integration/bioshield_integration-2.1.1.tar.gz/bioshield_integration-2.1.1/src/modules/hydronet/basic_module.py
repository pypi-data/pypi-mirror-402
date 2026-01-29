"""
Basic HydroNet module
Provides water metrics for BioShield
"""

def get_water_metrics():
    """Get water metrics from HydroNet"""
    return {
        'svi': 0.25,
        'quality': 85,
        'contamination': 15,
        'source': 'simulated'
    }

__all__ = ['get_water_metrics']
