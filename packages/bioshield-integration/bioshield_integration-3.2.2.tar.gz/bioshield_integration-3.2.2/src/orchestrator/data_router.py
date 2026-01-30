#!/usr/bin/env python3
"""
Data Router
Manages data flow between A, AB, B, C, D levels

File: orchestrator/data_router.py
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List


class DataRouter:
    """
    Routes data between different BioShield levels
    Handles data validation, transformation, and persistence
    """
    
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        
        # Data directories
        self.data_dir = base_dir / "data" / "routing"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Route logs
        self.route_log = self.data_dir / "route_log.json"
        self.routes = self._load_routes()
        
        print("📡 Data Router initialized")
    
    def _load_routes(self) -> List[Dict]:
        """Load routing history"""
        if self.route_log.exists():
            try:
                with open(self.route_log, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def _save_routes(self):
        """Save routing history"""
        try:
            # Keep last 1000 routes
            routes_to_save = self.routes[-1000:]
            with open(self.route_log, 'w', encoding='utf-8') as f:
                json.dump(routes_to_save, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Error saving routes: {e}")
    
    def route_a_to_b(self, a_data: Dict) -> Dict:
        """
        Route data from A_HydroNet to B_Agro_Immunity
        
        Transformation:
        - svi → B4_hydro_agro_sync
        - water_quality → B5_irrigation_efficiency (inverted)
        - contamination → B6_water_quality_impact
        """
        transformed = {
            'B4_hydro_agro_sync': a_data.get('svi', 0),
            'B5_irrigation_efficiency': 100 - a_data.get('quality', 100),
            'B6_water_quality_impact': a_data.get('contamination', 0),
            'water_availability_index': a_data.get('flow_rate', 150) / 150.0,
            'source': 'A_HydroNet',
            'routed_at': datetime.now().isoformat()
        }
        
        self._log_route('A', 'B', a_data, transformed)
        
        return transformed
    
    def route_b_to_c(self, b_data: Dict) -> Dict:
        """
        Route data from B_Agro_Immunity to C_Pathogen_Intel (future)
        
        Transformation:
        - Genetic stress → Pathogen susceptibility
        - Soil health → Immune capacity
        """
        transformed = {
            'pathogen_susceptibility': 1.0 - b_data.get('immunity_strength', 0.5),
            'immune_capacity': b_data.get('health_score', 0.5),
            'genetic_vulnerability': b_data.get('genetic_stress_trigger', False),
            'source': 'B_Agro_Immunity',
            'routed_at': datetime.now().isoformat()
        }
        
        self._log_route('B', 'C', b_data, transformed)
        
        return transformed
    
    def route_c_to_d(self, c_data: Dict) -> Dict:
        """
        Route data from C_Pathogen_Intel to D_Crypto_Infra (future)
        
        Transformation:
        - Pathogen alerts → Encrypted threats
        - Surveillance data → Secure intelligence
        """
        transformed = {
            'threat_level': c_data.get('pathogen_risk', 'LOW'),
            'intelligence_data': c_data.get('surveillance_data', {}),
            'encryption_required': True,
            'source': 'C_Pathogen_Intel',
            'routed_at': datetime.now().isoformat()
        }
        
        self._log_route('C', 'D', c_data, transformed)
        
        return transformed
    
    def broadcast(self, data: Dict, targets: List[str]) -> Dict:
        """
        Broadcast data to multiple targets
        
        Args:
            data: Data to broadcast
            targets: List of target levels ['A', 'B', 'C', 'D']
        
        Returns:
            Dictionary of results per target
        """
        results = {}
        
        for target in targets:
            results[target] = {
                'data': data.copy(),
                'timestamp': datetime.now().isoformat(),
                'status': 'delivered'
            }
        
        self._log_broadcast(data, targets)
        
        return results
    
    def validate_data(self, data: Dict, level: str) -> bool:
        """
        Validate data format for specific level
        
        Args:
            data: Data to validate
            level: Target level ('A', 'B', 'C', 'D')
        
        Returns:
            True if valid, False otherwise
        """
        validators = {
            'A': self._validate_a_data,
            'B': self._validate_b_data,
            'C': self._validate_c_data,
            'D': self._validate_d_data
        }
        
        validator = validators.get(level)
        if validator:
            return validator(data)
        
        return False
    
    def _validate_a_data(self, data: Dict) -> bool:
        """Validate A_HydroNet data"""
        required = ['svi', 'quality']
        return all(key in data for key in required)
    
    def _validate_b_data(self, data: Dict) -> bool:
        """Validate B_Agro_Immunity data"""
        required = ['bacteria_species', 'nutrients']
        return all(key in data for key in required)
    
    def _validate_c_data(self, data: Dict) -> bool:
        """Validate C_Pathogen_Intel data"""
        # Future implementation
        return True
    
    def _validate_d_data(self, data: Dict) -> bool:
        """Validate D_Crypto_Infra data"""
        # Future implementation
        return True
    
    def _log_route(self, source: str, target: str, 
                   original: Dict, transformed: Dict):
        """Log data route"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'route': f"{source} → {target}",
            'original_keys': list(original.keys()),
            'transformed_keys': list(transformed.keys()),
            'size_bytes': len(json.dumps(transformed))
        }
        
        self.routes.append(log_entry)
        self._save_routes()
    
    def _log_broadcast(self, data: Dict, targets: List[str]):
        """Log broadcast operation"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'type': 'broadcast',
            'targets': targets,
            'data_keys': list(data.keys())
        }
        
        self.routes.append(log_entry)
        self._save_routes()
    
    def get_routing_stats(self) -> Dict:
        """Get routing statistics"""
        if not self.routes:
            return {'total_routes': 0}
        
        routes_by_type = {}
        for route in self.routes:
            route_type = route.get('route', route.get('type', 'unknown'))
            routes_by_type[route_type] = routes_by_type.get(route_type, 0) + 1
        
        return {
            'total_routes': len(self.routes),
            'routes_by_type': routes_by_type,
            'last_route': self.routes[-1] if self.routes else None
        }
    
    def export_routing_report(self, filepath: str = None):
        """Export routing report"""
        if not filepath:
            reports_dir = self.base_dir / "reports"
            reports_dir.mkdir(parents=True, exist_ok=True)
            filepath = reports_dir / "routing_report.json"
        else:
            filepath = Path(filepath)
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'statistics': self.get_routing_stats(),
            'recent_routes': self.routes[-50:]
        }
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            print(f"📄 Routing report exported to {filepath}")
        except Exception as e:
            print(f"❌ Error exporting report: {e}")
        
        return report


# ============================================================
# TESTING
# ============================================================

def test_data_router():
    """Test data routing"""
    print("\n" + "="*60)
    print("🧪 TESTING DATA ROUTER")
    print("="*60 + "\n")
    
    router = DataRouter(Path(__file__).parent.parent)
    
    # Test A → B route
    print("📡 Testing A → B route...")
    a_data = {
        'svi': 0.38,
        'quality': 62,
        'contamination': 28,
        'flow_rate': 95
    }
    
    b_data = router.route_a_to_b(a_data)
    print(f"✅ Transformed: {list(b_data.keys())}")
    
    # Test B → C route
    print("\n📡 Testing B → C route...")
    b_state = {
        'immunity_strength': 0.72,
        'health_score': 0.65,
        'genetic_stress_trigger': True
    }
    
    c_data = router.route_b_to_c(b_state)
    print(f"✅ Transformed: {list(c_data.keys())}")
    
    # Test broadcast
    print("\n📡 Testing broadcast...")
    broadcast_data = {'alert': 'HIGH_STRESS', 'svi': 0.45}
    results = router.broadcast(broadcast_data, ['A', 'B', 'C'])
    print(f"✅ Broadcast to: {list(results.keys())}")
    
    # Show stats
    print("\n📊 Routing Statistics:")
    stats = router.get_routing_stats()
    print(f"   Total Routes: {stats['total_routes']}")
    print(f"   Routes by Type: {stats['routes_by_type']}")
    
    # Export report
    router.export_routing_report()
    
    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    test_data_router()
