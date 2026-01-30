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
Adaptive Memory System - Phase 1
Cross-platform adaptive memory system

File: adaptive_memory.py
"""

import json
import time
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import numpy as np


class AdaptiveMemory:
    """
    Memory system that learns from alert history
    """
    
    def __init__(self, component_name: str = "shared", memory_path: str = None):
        # Get current directory where this file is located
        current_dir = Path(__file__).parent
        
        self.component = component_name
        
        # Set correct memory path
        if memory_path:
            self.memory_path = Path(memory_path)
        else:
            # Create memory directory relative to current location
            memory_dir = current_dir / "data" / "memory"
            memory_dir.mkdir(parents=True, exist_ok=True)
            self.memory_path = memory_dir / f"adaptive_memory_{component_name}.json"
        
        # Set reports path relative to current location
        self.reports_dir = current_dir / "reports"
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        # Create directories
        self.memory_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing memory or initialize
        self.memory = self._load_memory()
        
        # Performance tracking
        self.stats = {
            'total_cycles': 0,
            'true_positives': 0,
            'false_positives': 0,
            'true_negatives': 0,
            'false_negatives': 0
        }
        
        # Dynamic thresholds (start with defaults)
        self.thresholds = {
            'svi_critical': 0.35,
            'svi_warning': 0.25,
            'quality_critical': 60,
            'contamination_critical': 30
        }
        
        # Temporal drift tracking
        self.drift_tracker = {
            'svi_trend': [],
            'quality_trend': [],
            'last_3_averages': [],
            'drift_detected': False,
            'drift_score': 0.0
        }
        
        print("✅ Adaptive Memory initialized")
        print(f"📊 Component: {component_name}")
        print(f"📁 Memory path: {self.memory_path}")
        print(f"📊 Historical cycles: {len(self.memory.get('cycles', []))}")
    
    def _load_memory(self) -> Dict:
        """Load memory from disk"""
        if self.memory_path.exists():
            try:
                with open(self.memory_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ Error loading memory: {e}, starting fresh")
                return self._create_new_memory()
        return self._create_new_memory()
    
    def _create_new_memory(self) -> Dict:
        """Create new memory structure"""
        return {
            'component': self.component,
            'cycles': [],
            'threshold_history': [],
            'created_at': datetime.now().isoformat(),
            'version': '1.0.0'
        }
    
    def _save_memory(self):
        """Save memory to disk"""
        try:
            with open(self.memory_path, 'w', encoding='utf-8') as f:
                json.dump(self.memory, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"❌ Error saving memory: {e}")
    
    def record_cycle(self, 
                     alert_data: Dict, 
                     action_taken: str, 
                     outcome: Dict):
        """
        Record a complete alert cycle
        """
        cycle = {
            'timestamp': datetime.now().isoformat(),
            'alert': alert_data,
            'action': action_taken,
            'outcome': outcome,
            'thresholds_used': self.thresholds.copy()
        }
        
        self.memory['cycles'].append(cycle)
        self.stats['total_cycles'] += 1
        
        # Classify outcome
        self._classify_outcome(alert_data, action_taken, outcome)
        
        # Learn from outcome
        self._learn_from_cycle(cycle)
        
        # Temporal Drift Detection
        self._detect_temporal_drift(cycle)
        
        # Save to disk
        self._save_memory()
        
        print(f"📝 Cycle recorded: {action_taken} → {'✅ Success' if outcome['success'] else '❌ Failed'}")
    
    def _classify_outcome(self, alert_data: Dict, action: str, outcome: Dict):
        """Classify alert outcome into confusion matrix categories"""
        alert_fired = alert_data.get('svi', 0) > self.thresholds['svi_critical']
        action_needed = outcome.get('actual_damage', 0) > 20
        
        if alert_fired and action_needed:
            self.stats['true_positives'] += 1
        elif alert_fired and not action_needed:
            self.stats['false_positives'] += 1
            print("⚠️ False positive detected - threshold may be too low")
        elif not alert_fired and not action_needed:
            self.stats['true_negatives'] += 1
        else:
            self.stats['false_negatives'] += 1
            print("🚨 Missed alert! Threshold may be too high")
    
    def _learn_from_cycle(self, cycle: Dict):
        """Adjust thresholds based on cycle outcome"""
        svi = cycle['alert']['svi']
        success = cycle['outcome']['success']
        damage = cycle['outcome'].get('actual_damage', 0)
        
        old_threshold = self.thresholds['svi_critical']
        
        # False Positive: Alert fired but no real damage
        if svi > old_threshold and damage < 10:
            adjustment = +0.01
            self.thresholds['svi_critical'] += adjustment
            print(f"🔧 Threshold adjusted: {old_threshold:.3f} → {self.thresholds['svi_critical']:.3f} (less sensitive)")
        
        # False Negative: No alert but high damage occurred
        elif svi <= old_threshold and damage > 30:
            adjustment = -0.01
            self.thresholds['svi_critical'] += adjustment
            print(f"🔧 Threshold adjusted: {old_threshold:.3f} → {self.thresholds['svi_critical']:.3f} (more sensitive)")
        
        # True Positive: Small reinforcement
        elif svi > old_threshold and success and damage > 20:
            adjustment = -0.002
            self.thresholds['svi_critical'] += adjustment
        
        # Keep threshold in safe bounds
        self.thresholds['svi_critical'] = np.clip(
            self.thresholds['svi_critical'], 
            0.20, 0.45
        )
        
        # Record threshold evolution
        self.memory['threshold_history'].append({
            'timestamp': datetime.now().isoformat(),
            'svi_critical': self.thresholds['svi_critical'],
            'reason': 'learning_adjustment'
        })
    
    def _detect_temporal_drift(self, cycle: Dict):
        """Detect gradual system degradation by comparing cycles"""
        current_svi = cycle['alert'].get('svi', 0)
        current_quality = cycle['alert'].get('quality', 100)
        
        # Store last 5 values
        self.drift_tracker['svi_trend'].append(current_svi)
        self.drift_tracker['quality_trend'].append(current_quality)
        
        # Keep only last 5 cycles
        for key in ['svi_trend', 'quality_trend']:
            if len(self.drift_tracker[key]) > 5:
                self.drift_tracker[key] = self.drift_tracker[key][-5:]
        
        # Calculate drift if we have enough data
        if len(self.drift_tracker['svi_trend']) >= 3:
            recent_avg = np.mean(self.drift_tracker['svi_trend'][-3:])
            older_avg = np.mean(self.drift_tracker['svi_trend'][:-3]) if len(self.drift_tracker['svi_trend']) > 3 else recent_avg
            
            drift_amount = recent_avg - older_avg
            self.drift_tracker['drift_score'] = drift_amount * 100  # Percentage drift
            
            # Alert on significant negative drift
            if drift_amount > 0.02:  # 2% increase in SVI over time
                self.drift_tracker['drift_detected'] = True
                print(f"🚨 TEMPORAL DRIFT: SVI increasing by {drift_amount:.3f} per cycle")
                print(f"   Trend: {older_avg:.3f} → {recent_avg:.3f}")
            else:
                self.drift_tracker['drift_detected'] = False
    
    def get_adaptive_threshold(self, context: Optional[Dict] = None) -> float:
        """Get current adaptive threshold"""
        base_threshold = self.thresholds['svi_critical']
        
        if context and context.get('season') == 'planting':
            return base_threshold * 0.9
        
        return base_threshold
    
    def get_performance_metrics(self) -> Dict:
        """Calculate system performance metrics"""
        if self.stats['total_cycles'] == 0:
            return {'error': 'No cycles recorded yet'}
        
        precision = (
            self.stats['true_positives'] / 
            (self.stats['true_positives'] + self.stats['false_positives'])
            if (self.stats['true_positives'] + self.stats['false_positives']) > 0
            else 0
        )
        
        recall = (
            self.stats['true_positives'] / 
            (self.stats['true_positives'] + self.stats['false_negatives'])
            if (self.stats['true_positives'] + self.stats['false_negatives']) > 0
            else 0
        )
        
        f1_score = (
            2 * (precision * recall) / (precision + recall)
            if (precision + recall) > 0
            else 0
        )
        
        accuracy = (
            (self.stats['true_positives'] + self.stats['true_negatives']) /
            self.stats['total_cycles']
        )
        
        return {
            'precision': precision,
            'recall': recall,
            'f1_score': f1_score,
            'accuracy': accuracy,
            'total_cycles': self.stats['total_cycles'],
            'current_threshold': self.thresholds['svi_critical'],
            'stats': self.stats,
            'drift_detected': self.drift_tracker['drift_detected'],
            'drift_score': self.drift_tracker['drift_score'],
            'trend_data': {
                'svi_trend': self.drift_tracker['svi_trend'][-5:],
                'quality_trend': self.drift_tracker['quality_trend'][-5:]
            }
        }
    
    def get_recent_patterns(self, last_n: int = 10) -> List[Dict]:
        """Get recent alert patterns for analysis"""
        cycles = self.memory.get('cycles', [])
        return cycles[-last_n:] if len(cycles) > last_n else cycles
    
    def predict_alert_need(self, current_data: Dict) -> Dict:
        """Predict if an alert is truly needed based on historical patterns"""
        svi = current_data.get('svi', 0)
        threshold = self.get_adaptive_threshold()
        
        similar_cycles = [
            c for c in self.memory.get('cycles', [])
            if abs(c['alert']['svi'] - svi) < 0.05
        ]
        
        if len(similar_cycles) == 0:
            return {
                'alert_recommended': svi > threshold,
                'confidence': 0.5,
                'reasoning': 'No historical data for similar conditions'
            }
        
        successes = sum(1 for c in similar_cycles if c['outcome']['success'])
        confidence = successes / len(similar_cycles)
        
        recommend = svi > threshold and confidence > 0.6
        
        return {
            'alert_recommended': recommend,
            'confidence': confidence,
            'reasoning': f"Based on {len(similar_cycles)} similar cases ({confidence*100:.0f}% success rate)",
            'adaptive_threshold': threshold
        }
    
    def export_report(self, filepath: str = None):
        """Export comprehensive memory report"""
        if not filepath:
            filepath = self.reports_dir / f"memory_report_{self.component}.json"
        else:
            filepath = Path(filepath)
        
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'component': self.component,
            'performance': self.get_performance_metrics(),
            'threshold_evolution': self.memory.get('threshold_history', [])[-20:],
            'recent_cycles': self.get_recent_patterns(20),
            'current_thresholds': self.thresholds,
            'drift_analysis': {
                'detected': self.drift_tracker['drift_detected'],
                'score': self.drift_tracker['drift_score'],
                'trend': self.drift_tracker['svi_trend'][-5:]
            }
        }
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            print(f"📄 Report exported to {filepath}")
        except Exception as e:
            print(f"❌ Error exporting report: {e}")
        
        return report


# ============================================================
# TESTING & DEMONSTRATION
# ============================================================

def test_adaptive_memory():
    """Test the adaptive memory system"""
    print("\n" + "="*60)
    print("🧪 TESTING ADAPTIVE MEMORY SYSTEM")
    print("="*60 + "\n")
    
    # Initialize with component name
    memory = AdaptiveMemory(component_name="test")
    
    print(f"Initial threshold: {memory.thresholds['svi_critical']:.3f}\n")
    
    # Simulate cycles
    test_scenarios = [
        (0.38, 62, 'ACTIVATE_GENETIC_PROTECTION', True, 25),
        (0.40, 58, 'ACTIVATE_GENETIC_PROTECTION', True, 35),
        (0.36, 65, 'ACTIVATE_GENETIC_PROTECTION', True, 8),
        (0.42, 55, 'ACTIVATE_GENETIC_PROTECTION', True, 40),
        (0.37, 63, 'ACTIVATE_GENETIC_PROTECTION', True, 5),
        (0.33, 70, 'MONITOR', False, 32),
        (0.39, 60, 'ACTIVATE_GENETIC_PROTECTION', True, 28),
        (0.41, 57, 'ACTIVATE_GENETIC_PROTECTION', True, 38),
        (0.35, 68, 'ACTIVATE_GENETIC_PROTECTION', True, 12),
        (0.43, 54, 'ACTIVATE_GENETIC_PROTECTION', True, 45),
    ]
    
    for i, (svi, quality, action, success, damage) in enumerate(test_scenarios, 1):
        print(f"\n--- Cycle {i} ---")
        
        alert_data = {
            'svi': svi,
            'quality': quality,
            'contamination': 20 + i * 2
        }
        
        outcome = {
            'success': success,
            'actual_damage': damage,
            'response_time': 180
        }
        
        memory.record_cycle(alert_data, action, outcome)
        time.sleep(0.1)
    
    # Show performance
    print("\n" + "="*60)
    print("📊 PERFORMANCE METRICS")
    print("="*60)
    
    metrics = memory.get_performance_metrics()
    print(f"\n✅ Accuracy: {metrics['accuracy']*100:.1f}%")
    print(f"🎯 Precision: {metrics['precision']*100:.1f}%")
    print(f"📡 Recall: {metrics['recall']*100:.1f}%")
    print(f"⚖️ F1 Score: {metrics['f1_score']:.3f}")
    print(f"\n🔧 Final Threshold: {metrics['current_threshold']:.3f}")
    
    print(f"\n📊 Confusion Matrix:")
    print(f"  True Positives:  {metrics['stats']['true_positives']}")
    print(f"  False Positives: {metrics['stats']['false_positives']}")
    print(f"  True Negatives:  {metrics['stats']['true_negatives']}")
    print(f"  False Negatives: {metrics['stats']['false_negatives']}")
    
    # Test prediction
    print("\n" + "="*60)
    print("🔮 PREDICTION TEST")
    print("="*60)
    
    test_data = {'svi': 0.38, 'quality': 62}
    prediction = memory.predict_alert_need(test_data)
    
    print(f"\nCurrent data: SVI={test_data['svi']}")
    print(f"Alert recommended: {'✅ YES' if prediction['alert_recommended'] else '❌ NO'}")
    print(f"Confidence: {prediction['confidence']*100:.0f}%")
    print(f"Reasoning: {prediction['reasoning']}")
    print(f"Adaptive threshold: {prediction['adaptive_threshold']:.3f}")
    
    # Export report
    print("\n" + "="*60)
    memory.export_report()
    print("="*60 + "\n")


def integrate_with_ab_bridge():
    """Integration example with AB_Bridge"""
    print("\n" + "="*60)
    print("🔗 INTEGRATION WITH AB_BRIDGE")
    print("="*60)
    
    print("\n📋 Integration steps:")
    print("1. Import the module:")
    print("Integration test complete")
    print("\n2. Initialize in your bridge class:")
    print("   self.memory = AdaptiveMemory('aquacrop')")
    print("\n3. Record cycles after processing:")
    print("   self.memory.record_cycle(alert_data, action, outcome)")
    print("\n4. Use adaptive thresholds:")
    print("   threshold = self.memory.get_adaptive_threshold()")
    print("="*60)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--integrate":
        integrate_with_ab_bridge()
    else:
        test_adaptive_memory()
