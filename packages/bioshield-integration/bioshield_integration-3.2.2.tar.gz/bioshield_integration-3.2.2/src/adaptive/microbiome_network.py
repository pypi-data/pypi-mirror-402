import sys
import os

# حل مرن للمسارات
_current_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_current_dir)
_project_root = os.path.dirname(_parent_dir)

# إضافة جميع المسارات المحتملة
sys.path.insert(0, _current_dir)      # src/adaptive/
sys.path.insert(0, _parent_dir)       # src/
sys.path.insert(0, _project_root)     # BioShield-Integration/
sys.path.insert(0, os.path.join(_project_root, 'src'))  # BioShield-Integration/src/

#!/usr/bin/env python3
"""
Microbiome Network Analysis - Phase 2
Analyzes soil-plant-microbe networks using Transfer Entropy

File: microbiome_network.py
"""

import json
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import sys


class MicrobiomeNetwork:
    """
    Analyze biological networks using Transfer Entropy
    Same mathematical framework as HydroNet but for biological systems
    """
    
    def __init__(self, component_name: str = "shared"):
        current_dir = Path(__file__).parent
        
        self.component = component_name
        
        # Data storage
        self.data_dir = current_dir / "data" / "microbiome"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.network_file = self.data_dir / f"network_{component_name}.json"
        
        # Network state
        self.network_data = self._load_network()
        
        # Network metrics
        self.metrics = {
            'diversity_index': 0.0,
            'connectivity': 0.0,
            'resilience_score': 0.0,
            'immunity_strength': 0.0
        }
        
        print("✅ Microbiome Network initialized")
        print(f"📊 Component: {component_name}")
        print(f"📁 Data path: {self.data_dir}")
    
    def _load_network(self) -> Dict:
        """Load network data from disk"""
        if self.network_file.exists():
            try:
                with open(self.network_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ Error loading network: {e}, starting fresh")
                return self._create_new_network()
        return self._create_new_network()
    
    def _create_new_network(self) -> Dict:
        """Create new network structure"""
        return {
            'component': self.component,
            'nodes': [],
            'edges': [],
            'measurements': [],
            'created_at': datetime.now().isoformat(),
            'version': '1.0.0'
        }
    
    def _save_network(self):
        """Save network to disk"""
        try:
            with open(self.network_file, 'w', encoding='utf-8') as f:
                json.dump(self.network_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"❌ Error saving network: {e}")
    
    def calculate_shannon_diversity(self, species_counts: List[int]) -> float:
        """
        Calculate Shannon Diversity Index
        H = -Σ(pi * ln(pi))
        where pi = proportion of species i
        """
        if not species_counts or sum(species_counts) == 0:
            return 0.0
        
        total = sum(species_counts)
        proportions = [count / total for count in species_counts if count > 0]
        
        diversity = -sum(p * np.log(p) for p in proportions)
        
        return diversity
    
    def calculate_network_density(self, edges: List[Tuple], nodes: List[str]) -> float:
        """
        Calculate network density (connectivity)
        Density = 2 * E / (N * (N-1))
        where E = edges, N = nodes
        """
        n = len(nodes)
        if n <= 1:
            return 0.0
        
        e = len(edges)
        max_edges = n * (n - 1) / 2
        
        density = e / max_edges if max_edges > 0 else 0.0
        
        return density
    
    def calculate_transfer_entropy(self, source: np.ndarray, target: np.ndarray, 
                                   lag: int = 1) -> float:
        """
        Calculate Transfer Entropy (simplified)
        TE(X→Y) measures information flow from X to Y
        
        Similar to HydroNet's causality analysis
        """
        if len(source) < lag + 2 or len(target) < lag + 2:
            return 0.0
        
        try:
            # Discretize data
            source_bins = np.digitize(source, bins=np.percentile(source, [25, 50, 75]))
            target_bins = np.digitize(target, bins=np.percentile(target, [25, 50, 75]))
            
            # Calculate conditional probabilities (simplified)
            # Real TE requires more sophisticated calculation
            correlation = np.corrcoef(source_bins[:-lag], target_bins[lag:])[0, 1]
            
            # Map correlation to TE-like measure
            te = abs(correlation) * 0.5  # Normalized to 0-0.5 range
            
            return te
            
        except Exception as e:
            print(f"⚠️ Error calculating TE: {e}")
            return 0.0
    
    def analyze_soil_microbiome(self, soil_data: Dict) -> Dict:
        """
        Analyze soil microbiome health
        
        Args:
            soil_data: {
                'bacteria_species': [count1, count2, ...],
                'fungi_species': [count1, count2, ...],
                'nutrients': {'N': val, 'P': val, 'K': val},
                'pH': float,
                'moisture': float
            }
        
        Returns:
            {
                'diversity': float,
                'health_score': float,
                'immunity_strength': float,
                'recommendations': []
            }
        """
        # Calculate diversity
        bacteria_div = self.calculate_shannon_diversity(
            soil_data.get('bacteria_species', [])
        )
        fungi_div = self.calculate_shannon_diversity(
            soil_data.get('fungi_species', [])
        )
        
        overall_diversity = (bacteria_div + fungi_div) / 2
        
        # Calculate health score (0-1)
        ph = soil_data.get('pH', 7.0)
        moisture = soil_data.get('moisture', 50)
        
        ph_score = 1.0 - abs(ph - 6.5) / 3.0  # Optimal pH = 6.5
        ph_score = max(0, min(1, ph_score))
        
        moisture_score = min(moisture / 60, 1.0)  # Optimal ~60%
        
        nutrient_score = self._calculate_nutrient_score(
            soil_data.get('nutrients', {})
        )
        
        health_score = (
            overall_diversity * 0.3 +
            ph_score * 0.2 +
            moisture_score * 0.2 +
            nutrient_score * 0.3
        )
        
        # Calculate immunity strength
        # High diversity + good health = strong immunity
        immunity = (overall_diversity * health_score) ** 0.5
        
        # Update metrics
        self.metrics['diversity_index'] = overall_diversity
        self.metrics['immunity_strength'] = immunity
        
        # Generate recommendations
        recommendations = []
        if overall_diversity < 2.0:
            recommendations.append("Increase microbial diversity through organic matter")
        if ph_score < 0.6:
            recommendations.append(f"Adjust pH (current: {ph:.1f}, optimal: 6.5)")
        if moisture_score < 0.5:
            recommendations.append("Increase soil moisture")
        if nutrient_score < 0.6:
            recommendations.append("Balance NPK nutrients")
        
        result = {
            'diversity': overall_diversity,
            'health_score': health_score,
            'immunity_strength': immunity,
            'ph_score': ph_score,
            'moisture_score': moisture_score,
            'nutrient_score': nutrient_score,
            'recommendations': recommendations
        }
        
        # Store measurement
        self.network_data['measurements'].append({
            'timestamp': datetime.now().isoformat(),
            'result': result
        })
        self._save_network()
        
        return result
    
    def _calculate_nutrient_score(self, nutrients: Dict) -> float:
        """Calculate nutrient balance score"""
        if not nutrients:
            return 0.5
        
        # Optimal ranges (example values)
        optimal = {'N': 40, 'P': 30, 'K': 40}
        
        scores = []
        for key in ['N', 'P', 'K']:
            if key in nutrients and key in optimal:
                value = nutrients[key]
                opt = optimal[key]
                # Score based on deviation from optimal
                score = 1.0 - min(abs(value - opt) / opt, 1.0)
                scores.append(score)
        
        return sum(scores) / len(scores) if scores else 0.5
    
    def calculate_biological_svi(self, current_state: Dict) -> float:
        """
        Calculate System Vulnerability Index for biological system
        Similar to HydroNet SVI but for microbiome
        
        SVI = weighted sum of vulnerability indicators
        High SVI = High vulnerability (bad)
        """
        soil_health = current_state.get('health_score', 0.5)
        diversity = current_state.get('diversity', 1.0)
        immunity = current_state.get('immunity_strength', 0.5)
        
        # Convert to vulnerability (inverse of health)
        health_vuln = 1.0 - soil_health
        diversity_vuln = 1.0 - min(diversity / 3.0, 1.0)  # Max diversity ~3
        immunity_vuln = 1.0 - immunity
        
        # Weighted SVI
        svi = (
            health_vuln * 0.4 +
            diversity_vuln * 0.3 +
            immunity_vuln * 0.3
        )
        
        return svi
    
    def predict_collapse_risk(self, time_series: List[Dict]) -> Dict:
        """
        Predict risk of microbiome collapse
        Based on trend analysis of health indicators
        
        Args:
            time_series: List of measurements over time
        
        Returns:
            {
                'risk_level': 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL',
                'svi': float,
                'trend': 'improving' | 'stable' | 'degrading',
                'time_to_collapse': int (months) or None
            }
        """
        if len(time_series) < 3:
            return {
                'risk_level': 'UNKNOWN',
                'svi': 0.0,
                'trend': 'stable',
                'time_to_collapse': None
            }
        
        # Extract health scores
        health_scores = [m['result']['health_score'] for m in time_series]
        
        # Calculate trend
        recent = health_scores[-3:]
        trend_value = (recent[-1] - recent[0]) / len(recent)
        
        if trend_value > 0.05:
            trend = 'improving'
        elif trend_value < -0.05:
            trend = 'degrading'
        else:
            trend = 'stable'
        
        # Calculate current SVI
        current_svi = self.calculate_biological_svi(time_series[-1]['result'])
        
        # Determine risk level
        if current_svi > 0.70:
            risk_level = 'CRITICAL'
        elif current_svi > 0.50:
            risk_level = 'HIGH'
        elif current_svi > 0.30:
            risk_level = 'MEDIUM'
        else:
            risk_level = 'LOW'
        
        # Predict time to collapse (if degrading)
        time_to_collapse = None
        if trend == 'degrading' and trend_value < 0:
            # Extrapolate: months until health reaches critical (0.2)
            current_health = health_scores[-1]
            if current_health > 0.2:
                months = int((current_health - 0.2) / abs(trend_value))
                time_to_collapse = max(1, min(months, 12))
        
        return {
            'risk_level': risk_level,
            'svi': current_svi,
            'trend': trend,
            'time_to_collapse': time_to_collapse,
            'current_health': health_scores[-1]
        }
    
    def get_network_metrics(self) -> Dict:
        """Get current network metrics"""
        return {
            'diversity_index': self.metrics['diversity_index'],
            'immunity_strength': self.metrics['immunity_strength'],
            'total_measurements': len(self.network_data['measurements']),
            'component': self.component
        }
    
    def export_analysis(self, filepath: str = None):
        """Export network analysis"""
        if not filepath:
            reports_dir = Path(__file__).parent / "reports"
            reports_dir.mkdir(parents=True, exist_ok=True)
            filepath = reports_dir / f"microbiome_analysis_{self.component}.json"
        else:
            filepath = Path(filepath)
        
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'component': self.component,
            'metrics': self.get_network_metrics(),
            'recent_measurements': self.network_data['measurements'][-10:],
            'risk_assessment': self.predict_collapse_risk(
                self.network_data['measurements']
            ) if len(self.network_data['measurements']) >= 3 else None
        }
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            print(f"📄 Analysis exported to {filepath}")
        except Exception as e:
            print(f"❌ Error exporting analysis: {e}")
        
        return report


# ============================================================
# TESTING
# ============================================================

def test_microbiome_network():
    """Test microbiome network analysis"""
    print("\n" + "="*60)
    print("🧪 TESTING MICROBIOME NETWORK")
    print("="*60 + "\n")
    
    network = MicrobiomeNetwork(component_name="test")
    
    # Simulate soil data
    test_data = {
        'bacteria_species': [120, 85, 200, 45, 90, 150, 30],
        'fungi_species': [60, 40, 80, 25, 55],
        'nutrients': {'N': 38, 'P': 28, 'K': 42},
        'pH': 6.7,
        'moisture': 55
    }
    
    print("📊 Analyzing soil microbiome...")
    result = network.analyze_soil_microbiome(test_data)
    
    print(f"\n✅ Diversity Index: {result['diversity']:.3f}")
    print(f"💚 Health Score: {result['health_score']*100:.1f}%")
    print(f"🛡️ Immunity Strength: {result['immunity_strength']*100:.1f}%")
    print(f"📈 pH Score: {result['ph_score']*100:.1f}%")
    print(f"💧 Moisture Score: {result['moisture_score']*100:.1f}%")
    print(f"🌿 Nutrient Score: {result['nutrient_score']*100:.1f}%")
    
    if result['recommendations']:
        print(f"\n📋 Recommendations:")
        for i, rec in enumerate(result['recommendations'], 1):
            print(f"  {i}. {rec}")
    
    # Calculate SVI
    print(f"\n🎯 Biological SVI: {network.calculate_biological_svi(result):.3f}")
    
    # Simulate time series for risk prediction
    print("\n" + "="*60)
    print("🔮 COLLAPSE RISK PREDICTION")
    print("="*60)
    
    # Add more measurements with degrading trend
    for i in range(5):
        degraded_data = test_data.copy()
        degraded_data['bacteria_species'] = [max(1, c - i*10) for c in test_data['bacteria_species']]
        degraded_data['pH'] = 6.7 - i * 0.2
        
        result = network.analyze_soil_microbiome(degraded_data)
    
    # Predict risk
    risk = network.predict_collapse_risk(network.network_data['measurements'])
    
    print(f"\n⚠️ Risk Level: {risk['risk_level']}")
    print(f"📊 Current SVI: {risk['svi']:.3f}")
    print(f"📈 Trend: {risk['trend']}")
    print(f"💚 Current Health: {risk['current_health']*100:.1f}%")
    if risk['time_to_collapse']:
        print(f"⏰ Time to Collapse: ~{risk['time_to_collapse']} months")
    
    # Export analysis
    print("\n" + "="*60)
    network.export_analysis()
    print("="*60 + "\n")


if __name__ == "__main__":
    test_microbiome_network()
