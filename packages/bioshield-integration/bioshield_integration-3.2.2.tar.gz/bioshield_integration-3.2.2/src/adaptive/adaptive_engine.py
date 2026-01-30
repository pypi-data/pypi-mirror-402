#!/usr/bin/env python3
"""
Adaptive Decision Engine - النسخة الكاملة
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import numpy as np

try:
    from .adaptive_memory import AdaptiveMemory
    from .microbiome_network import MicrobiomeNetwork
    from .adaptive_enhancements import AdaptiveEnhancements
except ImportError:
    from adaptive_memory import AdaptiveMemory
    from microbiome_network import MicrobiomeNetwork
    from adaptive_enhancements import AdaptiveEnhancements


class GeneticResilience:
    """تقيم المرونة الوراثية للمحاصيل"""
    
    def __init__(self):
        current_dir = Path(__file__).parent
        self.data_dir = current_dir / "data/genetics"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.profiles_file = self.data_dir / "genetic_profiles.json"
        self.profiles = self._load_profiles()
    
    def _load_profiles(self):
        """تحميل ملفات المرونة الوراثية"""
        if self.profiles_file.exists():
            try:
                with open(self.profiles_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return self._default_profiles()
        return self._default_profiles()
    
    def _default_profiles(self):
        """ملفات افتراضية للمحاصيل"""
        return {
            'wheat': {
                'drought_tolerance': 0.65,
                'pathogen_resistance': 0.70,
                'nutrient_efficiency': 0.60,
                'stress_genes': ['DHN1', 'LEA3', 'ABA2']
            },
            'corn': {
                'drought_tolerance': 0.55,
                'pathogen_resistance': 0.60,
                'nutrient_efficiency': 0.75,
                'stress_genes': ['ZmDREB2A', 'ZmNAC111']
            },
            'rice': {
                'drought_tolerance': 0.45,
                'pathogen_resistance': 0.65,
                'nutrient_efficiency': 0.70,
                'stress_genes': ['OsDREB1', 'OsLEA3']
            }
        }
    
    def calculate_resilience_score(self, crop_type: str, stress_type: str):
        """حساب درجة المرونة الوراثية"""
        crop_type = crop_type.lower()
        
        if crop_type not in self.profiles:
            return {
                'score': 0.5,
                'recommended_threshold': 0.35,
                'stress_genes': [],
                'confidence': 0.3
            }
        
        profile = self.profiles[crop_type]
        
        # تحديد نوع الضغط
        trait_map = {
            'drought': 'drought_tolerance',
            'pathogen': 'pathogen_resistance',
            'nutrient': 'nutrient_efficiency',
            'general': 'average'
        }
        
        trait = trait_map.get(stress_type, 'average')
        
        if trait == 'average':
            score = np.mean([
                profile['drought_tolerance'],
                profile['pathogen_resistance'],
                profile['nutrient_efficiency']
            ])
        else:
            score = profile[trait]
        
        recommended_threshold = 0.35 * (1 + score * 0.3)
        
        return {
            'score': score,
            'recommended_threshold': recommended_threshold,
            'stress_genes': profile.get('stress_genes', []),
            'confidence': 0.8
        }


class AdaptiveEngine:
    """المحرك التكيفي الرئيسي"""
    
    def __init__(self, component_name="shared"):
        self.component = component_name
        print("🔧 Initializing Adaptive Engine...")
        
        self.memory = AdaptiveMemory(component_name)
        self.microbiome = MicrobiomeNetwork(component_name)
        self.genetics = GeneticResilience()  # ✅ أضفنا الكلاس
        self.enhancer = AdaptiveEnhancements()
        
        current_dir = Path(__file__).parent
        self.history_dir = current_dir / "data/decisions"
        self.history_dir.mkdir(parents=True, exist_ok=True)
        self.history_file = self.history_dir / f"decisions_{component_name}.json"
        self.decision_history = self._load_history()
        
        print("✅ Adaptive Engine ready")
    
    def _load_history(self):
        """تحميل تاريخ القرارات"""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def decide_intervention(self, water_data: Dict, soil_data: Dict, crop_data: Dict):
        """اتخاذ قرار ذكي"""
        print("\n" + "="*60)
        print("🎯 ADAPTIVE DECISION ENGINE")
        print("="*60)
        
        adaptive_threshold = self.memory.get_adaptive_threshold()
        svi = water_data.get('svi', 0)
        base_alert = svi > adaptive_threshold
        
        print(f"\n📊 Memory: SVI={svi:.3f}, Threshold={adaptive_threshold:.3f}, Alert={'🚨 YES' if base_alert else '✅ NO'}")
        
        soil_analysis = self.microbiome.analyze_soil_microbiome(soil_data)
        immunity_strength = soil_analysis['immunity_strength']
        health_score = soil_analysis['health_score']
        
        print(f"\n📊 Microbiome: Immunity={immunity_strength*100:.1f}%, Health={health_score*100:.1f}%")
        
        crop_type = crop_data.get('type', 'wheat')
        stress_type = self._infer_stress_type(water_data)
        resilience = self.genetics.calculate_resilience_score(crop_type, stress_type)
        genetic_score = resilience['score']
        
        print(f"\n📊 Genetics: Crop={crop_type}, Score={genetic_score*100:.1f}%")
        
        water_stress = svi / adaptive_threshold if adaptive_threshold > 0 else 0
        bio_buffer = immunity_strength * health_score
        
        # حساب واقعي للضغط
        if svi < 0.25:
            stress_burden = 0.1  # منخفض جداً
        elif svi < 0.35:
            stress_burden = 0.3  # متوسط
        else:
            stress_burden = 0.7  # مرتفع
        
        # معادلة قرار متوازنة
        intervention_score = (
            water_stress * 0.5 -      # تأثير الماء
            bio_buffer * 0.3 +         # تأثير المناعة
            stress_burden * 0.2        # تأثير تراكم الضغط
        )
        
        print(f"\n🎯 Factors: Water={water_stress:.2f}, Bio={bio_buffer:.2f}, Stress={stress_burden:.2f}, Score={intervention_score:.2f}")
        
        # عتبات قرار واقعية
        if intervention_score > 0.6:
            action = "CRITICAL_INTERVENTION"
            reasoning = "High stress score requires immediate intervention"
        elif intervention_score > 0.3:
            action = "MONITOR_CLOSELY"
            reasoning = "Moderate stress level - close monitoring needed"
        elif intervention_score > 0.1:
            action = "PREVENTIVE_ACTION"
            reasoning = "Low stress - preventive measures recommended"
        else:
            action = "NORMAL_OPERATIONS"
            reasoning = "System operating within normal parameters"
        
        # ثقة ثابتة مؤقتاً
        confidence = 0.7
        
        decision = {
            'action': action,
            'confidence': confidence,
            'reasoning': reasoning,
            'factors': {
                'water_stress': water_stress,
                'bio_buffer': bio_buffer,
                'stress_burden': stress_burden,
                'intervention_score': intervention_score,
                'genetic_score': genetic_score
            }
        }
        
        print(f"\n{'='*60}\n🎯 DECISION: {action}, Confidence={confidence*100:.0f}%\n{'='*60}")
        
        return decision
    
    def _infer_stress_type(self, water_data: Dict):
        """تحديد نوع الضغط من بيانات الماء"""
        svi = water_data.get('svi', 0)
        quality = water_data.get('quality', 100)
        contamination = water_data.get('contamination', 0)
        
        if svi > 0.35:
            return 'drought'
        elif quality < 60:
            return 'nutrient'
        elif contamination > 25:
            return 'pathogen'
        else:
            return 'general'
    
    def record_outcome(self, decision: Dict, actual_outcome: Dict):
        """تسجيل النتيجة الفعلية للتعلم"""
        self.memory.record_cycle(decision['factors'], decision['action'], actual_outcome)
        print("✅ Outcome recorded for learning")
    
    def get_system_status(self):
        """الحصول على حالة النظام"""
        return {
            'component': self.component,
            'memory': self.memory.get_performance_metrics(),
            'microbiome': self.microbiome.get_network_metrics(),
            'decisions': len(self.decision_history)
        }
