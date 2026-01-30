#!/usr/bin/env python3
"""
smart_executor_wrapper.py - Smart Executor with Feedback Loop
Final fixed version with proper recommendations
"""

import json
import hashlib
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional


class BasicCryptoModule:
    """Basic cryptographic operations"""
    
    def __init__(self):
        self.name = "BasicCryptoModule"
        self.version = "2.0"
    
    def calculate_hash(self, data: str) -> str:
        return hashlib.sha256(data.encode()).hexdigest()
    
    def timestamp_data(self, data: dict) -> dict:
        timestamped = data.copy()
        timestamped['timestamp'] = datetime.now().isoformat()
        timestamped['integrity_hash'] = self.calculate_hash(
            json.dumps(timestamped, sort_keys=True)
        )
        return timestamped


class SmartExecutorDPlus:
    """Module D+ - Smart Decision Executor"""
    
    def __init__(self):
        self.name = "SmartExecutorDPlus"
        self.version = "3.1.0"
        self.position = "Module D+"
        
        self.crypto = BasicCryptoModule()
        self.current_svi = 1.0
        self.current_immunity = 0.7
        self.stuck_counter = 0
        self.decision_history = []
        
        print(f"🚀 {self.name} v{self.version}")
        print(f"📍 {self.position} - Smart Execution System")
        print("✅ Ready to execute decisions")
        print(f"📊 Initial State: SVI={self.current_svi}, Immunity={self.current_immunity}")
    
    def execute_pipeline(self, c_data: Dict) -> Dict:
        """Execute complete smart pipeline"""
        print(f"\n{'='*60}")
        print(f"{self.name}: Starting Smart Pipeline")
        print(f"{'='*60}")
        
        c_decision = self._analyze_decision(c_data)
        print(f"📥 Module C Decision: {c_decision['type']}")
        print(f"   SVI: {c_decision['svi']:.1f}, Immunity: {c_decision['immunity']:.1f}")
        
        if self._is_decision_stuck(c_decision):
            print(f"⚠️  STUCK DECISION DETECTED! Count: {self.stuck_counter}")
            c_decision = self._adapt_decision(c_decision)
        
        print(f"\n⚡ [1/4] Executing Decision...")
        execution = self._execute_decision(c_decision)
        
        print(f"\n📊 [2/4] Monitoring Results...")
        results = self._monitor_results(execution)
        
        print(f"\n🔄 [3/4] Processing Feedback Loop...")
        feedback = self._process_feedback(c_decision, results)
        
        print(f"\n🔐 [4/4] Secure Logging (+1)...")
        secure_log = self._create_secure_log({
            "decision": c_decision,
            "execution": execution,
            "results": results,
            "feedback": feedback
        })
        
        self._update_state(results)
        report = self._generate_report(c_decision, execution, results, feedback, secure_log)
        
        print(f"\n✅ Smart Pipeline Complete!")
        print(f"📈 New SVI: {self.current_svi:.1f}")
        print(f"🛡️  New Immunity: {self.current_immunity:.1f}")
        
        return report
    
    def _analyze_decision(self, c_data: Dict) -> Dict:
        return {
            "timestamp": datetime.now().isoformat(),
            "type": c_data.get('summary', {}).get('dominant_scenario', 'UNKNOWN'),
            "svi": c_data.get('state', {}).get('water_stress', self.current_svi),
            "immunity": c_data.get('state', {}).get('immunity_level', self.current_immunity),
            "confidence": c_data.get('summary', {}).get('certainty', 0.0),
            "cycle": c_data.get('cycle', 0)
        }
    
    def _is_decision_stuck(self, decision: Dict) -> bool:
        if len(self.decision_history) >= 2:
            last_types = [h.get('type') for h in self.decision_history[-2:]]
            if all(t == decision['type'] for t in last_types):
                self.stuck_counter += 1
                return True
        return False
    
    def _adapt_decision(self, decision: Dict) -> Dict:
        print(f"🔄 Adapting stuck decision...")
        adapted = decision.copy()
        if decision['type'] == 'CRITICAL_INTERVENTION':
            adapted['type'] = 'ADAPTIVE_CRITICAL'
            adapted['strategy'] = 'phased_reduction'
        self.stuck_counter = 0
        return adapted
    
    def _execute_decision(self, decision: Dict) -> Dict:
        actions = []
        if decision['type'] in ['CRITICAL_INTERVENTION', 'ADAPTIVE_CRITICAL']:
            actions = [
                {"action": "emergency_watering", "intensity": 0.8, "duration": 300},
                {"action": "nutrient_boost", "type": "defense", "amount": 0.5}
            ]
        return {
            "decision_type": decision['type'],
            "actions": actions,
            "execution_id": hashlib.md5(str(time.time()).encode()).hexdigest()[:8],
            "start_time": datetime.now().isoformat()
        }
    
    def _monitor_results(self, execution: Dict) -> Dict:
        return {
            "svi_reduction": 0.2,
            "immunity_improvement": 0.1,
            "actions_completed": len(execution.get('actions', [])),
            "completion_rate": 0.9,
            "monitoring_time": datetime.now().isoformat()
        }
    
    def _process_feedback(self, original_decision: Dict, results: Dict) -> Dict:
        effectiveness = 0.7
        if results.get('svi_reduction', 0) > 0.15:
            effectiveness += 0.1
        effectiveness = min(1.0, effectiveness)
        
        return {
            "original_decision": original_decision['type'],
            "effectiveness_score": effectiveness,
            "effectiveness_level": "HIGH" if effectiveness > 0.7 else "MEDIUM",
            "feedback_timestamp": datetime.now().isoformat()
        }
    
    def _create_secure_log(self, data: Dict) -> Dict:
        log_entry = {
            "index": len(self.decision_history) + 1,
            "timestamp": datetime.now().isoformat(),
            "data_hash": self.crypto.calculate_hash(json.dumps(data, sort_keys=True)),
            "decision_type": data.get('decision', {}).get('type', 'UNKNOWN'),
            "actions_count": len(data.get('execution', {}).get('actions', []))
        }
        self.decision_history.append(data.get('decision', {}))
        return log_entry
    
    def _update_state(self, results: Dict):
        self.current_svi = max(0.0, min(1.0, 
            self.current_svi - results.get('svi_reduction', 0)))
        self.current_immunity = max(0.0, min(1.0,
            self.current_immunity + results.get('immunity_improvement', 0)))
    
    def _generate_report(self, decision, execution, results, feedback, log):
        return {
            "system": self.name,
            "version": self.version,
            "execution_timestamp": datetime.now().isoformat(),
            "components_executed": 4,
            "system_state": {
                "current_svi": self.current_svi,
                "current_immunity": self.current_immunity,
                "stuck_counter": self.stuck_counter,
                "total_decisions": len(self.decision_history)
            },
            "decision_analysis": decision,
            "execution_summary": execution,
            "monitoring_results": results,
            "feedback_analysis": feedback,
            "secure_log_entry": log,
            "recommendations": self._get_system_recommendations()
        }
    
    def _get_system_recommendations(self) -> List[str]:
        recs = []
        if self.current_svi > 0.7:
            recs.append(f"CRITICAL: Reduce SVI from {self.current_svi:.1f} to below 0.5")
        if self.current_immunity < 0.85:
            recs.append(f"IMPORTANT: Improve immunity from {self.current_immunity:.1f} to above 0.85")
        if self.stuck_counter > 0:
            recs.append(f"Monitor stuck decisions: counter at {self.stuck_counter}")
        if not recs:
            recs.append("System operating normally")
        return recs
    
    def get_status(self) -> Dict:
        return {
            "module": self.name,
            "status": "OPERATIONAL",
            "svi": self.current_svi,
            "immunity": self.current_immunity,
            "decisions_processed": len(self.decision_history),
            "stuck_detections": self.stuck_counter
        }


if __name__ == "__main__":
    executor = SmartExecutorDPlus()
    
    test_c_data = {
        "summary": {
            "dominant_scenario": "CRITICAL_INTERVENTION",
            "certainty": 0.85
        },
        "state": {
            "water_stress": 1.0,
            "immunity_level": 0.7
        },
        "cycle": 12,
        "timestamp": "2026-01-20T18:24:48"
    }
    
    print("\n" + "="*60)
    print("🧪 TESTING SMART EXECUTOR SYSTEM")
    print("="*60)
    
    report = executor.execute_pipeline(test_c_data)
    
    print(f"\n📋 FINAL REPORT SUMMARY:")
    print(f"   SVI Change: 1.0 → {executor.current_svi:.1f}")
    print(f"   Immunity Change: 0.7 → {executor.current_immunity:.1f}")
    print(f"   Decisions Processed: {len(executor.decision_history)}")
    print(f"   System Status: {executor.get_status()['status']}")
    
    print(f"\n💡 RECOMMENDATIONS:")
    for i, rec in enumerate(report.get('recommendations', []), 1):
        print(f"   {i}. {rec}")
