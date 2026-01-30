#!/usr/bin/env python3
"""
Cascade Manager - Main orchestration for A→B→C→D flow
Uses LIVE WEB DATA from deployed websites
WITH MODULE C JSON INTEGRATION AND MODULE D+ CONNECTION
"""

import time
import json
import yaml
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import sys
import os

# Fix import path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = Path("/storage/emulated/0/Download/BioShield-Integration")
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

# Now import module wrappers with absolute path
try:
    from modules.hydronet import HydroNetWrapper
    from modules.aquacrop import AquaCropWrapper
    from modules.agro_immunity import AgroImmunityWrapper
    from modules.pathogen_intel.core.cascade_interface import CascadeInterfaceC
except ImportError as e:
    print(f"❌ Import error: {e}")
    print(f"📁 Project root: {project_root}")
    print(f"📁 Current dir: {current_dir}")
    print(f"🔍 Python path: {sys.path}")
    
    # Try alternative imports
    try:
        from src.modules.hydronet import HydroNetWrapper
        from src.modules.aquacrop import AquaCropWrapper
        from src.modules.agro_immunity import AgroImmunityWrapper
        print("✅ Successfully imported from src.modules")
    except ImportError as e2:
        print(f"❌ Alternative import failed: {e2}")
        raise

logger = logging.getLogger(__name__)


class CascadeManager:
    """Main orchestrator for BioShield cascade flow with LIVE WEB DATA"""
    
    def __init__(self, config_path: Optional[str] = None, use_live_web: bool = True):
        self.name = "BioShield_Orchestrator_Live"
        self.version = "6.0.0"
        self.use_live_web = use_live_web
        
        # Load configuration
        if config_path is None:
            config_path = project_root / "config" / "integration_config.yaml"
        self.config = self._load_config(str(config_path))
        
        # Initialize module wrappers WITH LIVE WEB
        print(f"🚀 Initializing Cascade Manager with LIVE WEB: {use_live_web}")
        
        self.hydronet = HydroNetWrapper(use_live_web=self.use_live_web)
        self.aquacrop = AquaCropWrapper()
        self.agro_immunity = AgroImmunityWrapper(use_live_web=self.use_live_web)
        
        # Initialize Pathogen Intel (Module C) - optional
        try:
            from modules.pathogen_intel.core.cascade_interface import CascadeInterfaceC
            self.pathogen_intel = CascadeInterfaceC()
            print("✅ Module C (Pathogen Intel) loaded successfully")
        except ImportError:
            print("⚠️ Module C (Pathogen Intel) not available, running without it")
            self.pathogen_intel = None
        
        # State tracking
        self.cascade_history = []
        self.last_run = None
        self.running = False
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        logger.info(f"{self.name} v{self.version} initialized")
        logger.info(f"🌐 Live Web Data: {'ENABLED' if self.use_live_web else 'DISABLED'}")
        logger.info(f"🔔 Alert System: ENABLED (Pipedream Webhook)")
    
    def _load_config(self, config_path: str) -> Dict:
        """Load YAML configuration file"""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return {
                'paths': {
                    'reports': 'reports',
                    'alerts': 'reports/alerts'
                }
            }
    
    def _get_module_c_summary(self):
        """Get summary from latest Module C JSON report - قراءة مباشرة من json/daily"""
        try:
            # المسار الصحيح داخل src
            c_reports_path = project_root / "src" / "modules" / "pathogen_intel" / "core" / "json" / "daily"
            
            if not c_reports_path.exists():
                print(f"ℹ️ Module C directory not found: {c_reports_path}")
                return None
            
            c_files = list(c_reports_path.glob("*.json"))
            
            if not c_files:
                print(f"ℹ️ No JSON files in: {c_reports_path}")
                return None
            
            latest = max(c_files, key=lambda x: x.stat().st_mtime)
            with open(latest, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # استخراج المعلومات الأساسية
            return {
                'file': latest.name,
                'path': str(latest),  # المسار الكامل للاستخدام الداخلي
                'cycle': data.get('cycle', 0),
                'dominant': data.get('summary', {}).get('dominant', 'UNKNOWN'),
                'certainty': data.get('summary', {}).get('certainty', 0.0),
                'timestamp': data.get('timestamp', ''),
                'scenarios': data.get('scenarios', []),
                'state': data.get('state', {})
            }
                
        except Exception as e:
            logger.debug(f"Module C read error: {e}")
            return None
    
    def _send_alert(self, record: Dict) -> None:
        """Send alert for critical status"""
        decision = record.get("final_decision", {}).get("action", "")
        
        print(f"🔔 DEBUG: _send_alert called with decision: {decision}")
        
        if decision == "CRITICAL_INTERVENTION":
            print("🚨 DEBUG: CRITICAL_INTERVENTION detected! Preparing alert...")
            
            alert_data = {
                "timestamp": record.get("timestamp", datetime.now().isoformat()),
                "alert_type": "CRITICAL",
                "water_svi": record.get("water_data", {}).get("svi", 0),
                "immunity_score": record.get("immunity_result", {}).get("immunity_score", 0),
                "confidence": record.get("final_decision", {}).get("confidence", 0),
                "message": "🚨 BioShield Alert: CRITICAL_INTERVENTION required",
                "system": "BioShield Cascade",
                "alert_id": f"BS-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            }
            
            print(f"📤 DEBUG: Sending alert data: {json.dumps(alert_data, indent=2)}")
            
            try:
                import requests
                print(f"🌐 DEBUG: Sending to Pipedream: https://eoi3vhd0zol7y5o.m.pipedream.net")
                response = requests.post(
                    "https://eoi3vhd0zol7y5o.m.pipedream.net",
                    json=alert_data,
                    timeout=5
                )
                print(f"✅ DEBUG: Alert sent successfully! Status: {response.status_code}")
                logger.info(f"Alert sent to Pipedream: {response.status_code}")
                
                # Also save alert locally
                self._log_alert_locally(alert_data)
                
            except ImportError:
                print("❌ DEBUG: requests module not installed!")
                logger.error("requests module not installed")
                self._fallback_alert(record)
            except Exception as e:
                print(f"❌ DEBUG: Failed to send alert: {e}")
                logger.error(f"Failed to send alert: {e}")
                self._fallback_alert(record)
        else:
            print(f"ℹ️ DEBUG: Not CRITICAL (decision: {decision}), skipping alert")
    
    def _log_alert_locally(self, alert_data: Dict) -> None:
        """Log alert locally as backup - TXT format only"""
        alert_dir = project_root / "reports" / "alerts"
        alert_dir.mkdir(exist_ok=True, parents=True)
        
        alert_time = datetime.fromisoformat(alert_data['timestamp'].replace('Z', '+00:00'))
        filename = f"alert_{alert_time.strftime('%Y%m%d_%H%M')}.txt"
        alert_file = alert_dir / filename
        
        with open(alert_file, 'w', encoding='utf-8') as f:
            f.write('=' * 50 + '\n')
            f.write('🚨 BioShield CRITICAL Alert\n')
            f.write('=' * 50 + '\n\n')
            f.write(f'Alert ID: {alert_data["alert_id"]}\n')
            f.write(f'Time: {alert_data["timestamp"]}\n')
            f.write(f'Alert Type: {alert_data["alert_type"]}\n')
            f.write(f'System: {alert_data["system"]}\n')
            f.write('\n' + '-' * 30 + '\n')
            f.write('📊 METRICS:\n')
            f.write(f'  Water SVI: {alert_data["water_svi"]:.3f}\n')
            f.write(f'  Immunity Score: {alert_data["immunity_score"]:.3f}\n')
            f.write(f'  Confidence: {alert_data["confidence"]:.0%}\n')
            f.write('\n' + '-' * 30 + '\n')
            f.write('💬 MESSAGE:\n')
            f.write(f'  {alert_data["message"]}\n')
            f.write('\n' + '=' * 50 + '\n')
        
        print(f"💾 DEBUG: Alert saved to: {alert_file}")
        
        log_file = alert_dir / "alerts.log"
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(
                f"[{alert_data['timestamp']}] CRITICAL | "
                f"SVI: {alert_data['water_svi']:.3f} | "
                f"Immunity: {alert_data['immunity_score']:.1f} | "
                f"Confidence: {alert_data['confidence']:.0%}\n"
            )
        
        logger.warning(f"🚨 CRITICAL alert saved: {filename}")
    
    def _fallback_alert(self, record: Dict) -> None:
        """Fallback alert system if webhook fails"""
        print("🔄 DEBUG: Using fallback alert system")
        alert_dir = project_root / "reports" / "alerts"
        alert_dir.mkdir(exist_ok=True, parents=True)
        
        now = datetime.now()
        filename = f"alert_fallback_{now.strftime('%Y%m%d_%H%M')}.txt"
        alert_file = alert_dir / filename
        
        with open(alert_file, 'w', encoding='utf-8') as f:
            f.write('=' * 50 + '\n')
            f.write('⚠️ BioShield Fallback Alert\n')
            f.write('=' * 50 + '\n\n')
            f.write(f'Time: {now.isoformat()}\n')
            f.write(f'Status: Webhook failed, using fallback\n')
            f.write(f'Water SVI: {record.get("water_data", {}).get("svi", 0):.3f}\n')
            f.write(f'Immunity Score: {record.get("immunity_result", {}).get("immunity_score", 0):.3f}\n')
            f.write('\n' + '=' * 50 + '\n')
        
        print(f"💾 DEBUG: Fallback alert saved to {alert_file}")
        logger.warning("🚨 CRITICAL ALERT LOGGED (Fallback)")
    
    def run_full_cascade(self) -> Dict[str, Any]:
        """Execute complete A→AB→B→C cascade with LIVE DATA"""
        self.running = True
        start_time = time.time()
        self.last_run = datetime.now()
        
        logger.info("Starting full cascade execution with LIVE WEB DATA")
        
        try:
            # Step 1: Get data from A_HydroNet (WITH LIVE WEB)
            print("🌊 Step 1: Querying A_HydroNet (Live Web Data)...")
            water_data = self.hydronet.get_current_state()
            print(f"   📊 HydroNet Data: SVI={water_data.get('svi', 'N/A')}, Source={water_data.get('source', 'unknown')}")
            
            # Step 2: Transform through AquaCrop (A→B)
            print("🔗 Step 2: Transforming through AquaCrop Bridge...")
            transformed_data = self.aquacrop.transform_a_to_b(water_data)
            
            # Step 3: Process with Agro_Immunity (B) (WITH LIVE WEB)
            print("🌱 Step 3: Analyzing with Agro_Immunity (Live Web Data)...")
            immunity_result = self.agro_immunity.get_immunity_strength()
            print(f"   📊 Agro Data: Immunity={immunity_result.get('immunity_score', 'N/A')}, Source={immunity_result.get('source', 'unknown')}")
            
            # Step 4: Process with Pathogen Intelligence (C) - if available
            pathogen_result = {"risk_level": "unknown", "risk_score": 0.0}
            if self.pathogen_intel:
                print("🧬 Step 4: Processing with Pathogen Intelligence...")
                try:
                    self.pathogen_intel.receive_from_b(immunity_result)
                    pathogen_result = self.pathogen_intel.receive_from_b({}) or pathogen_result
                    print(f"   📊 Pathogen Risk Level: {pathogen_result.get('risk_level', 'unknown')}")
                except Exception as e:
                    print(f"   ⚠️ Pathogen analysis error: {e}")
            else:
                print("   ⚠️ Module C (Pathogen Intel) not available")
            
            # ============ Get Module C data ============
            module_c_data = self._get_module_c_summary()
            if module_c_data:
                print(f"   📄 Module C Report: {module_c_data['file']}")
                print(f"   📊 Cycle: {module_c_data['cycle']}, Dominant: {module_c_data['dominant']}, Certainty: {module_c_data['certainty']:.2f}")
            
                # ============ CONNECT TO MODULE D+ ============
                try:
                    from modules.smart_executor.smart_executor_wrapper import SmartExecutorDPlus
                    module_d = SmartExecutorDPlus()
                    
                    d_input = {
                        "summary": {
                            "dominant_scenario": module_c_data.get("dominant", "UNKNOWN"),
                            "certainty": module_c_data.get("certainty", 0.0)
                        },
                        "state": {
                            "water_stress": water_data.get("svi", 0),
                            "immunity_level": immunity_result.get("immunity_score", 0)
                        },
                        "cycle": module_c_data.get("cycle", 0)
                    }
                    
                    d_result = module_d.execute_pipeline(d_input)
                    print(f"   🚀 Module D+ executed successfully")
                    
                    # Update water data with D+ results
                    if d_result and "system_state" in d_result:
                        water_data["svi"] = d_result["system_state"].get("current_svi", water_data.get("svi", 0))
                        immunity_result["immunity_score"] = d_result["system_state"].get("current_immunity", immunity_result.get("immunity_score", 0))
                        print(f"   📈 D+ Results: SVI={water_data['svi']:.1f}, Immunity={immunity_result['immunity_score']:.1f}")
                    
                except ImportError as e:
                    print(f"   ⚠️ Module D+ not available: {e}")
                except Exception as e:
                    print(f"   ⚠️ Module D+ execution error: {e}")
                # ============ END MODULE D+ ============
            # ============ END NEW ============
            
            # Step 5: Generate final decision
            print("🧠 Step 5: Generating adaptive decision...")
            final_decision = self._generate_decision(water_data, immunity_result)
            print(f"   🎯 Decision: {final_decision.get('action')} (Confidence: {final_decision.get('confidence', 0):.0%})")
            
            # Record history
            cascade_record = {
                'timestamp': datetime.now().isoformat(),
                'water_data': water_data,
                'transformed_data': transformed_data,
                'immunity_result': immunity_result,
                'pathogen_result': pathogen_result,
                'module_c_data': module_c_data,  # NEW: Add Module C data
                'final_decision': final_decision,
                'duration': time.time() - start_time,
                'data_sources': {
                    'hydro_source': water_data.get('source', 'unknown'),
                    'agro_source': immunity_result.get('source', 'unknown'),
                    'live_web_enabled': self.use_live_web
                }
            }
            self.cascade_history.append(cascade_record)
            
            # Save report
            self._save_report(cascade_record)
            
            # Send alert if CRITICAL
            print(f"🔍 DEBUG: Checking for CRITICAL alert...")
            print(f"🔍 DEBUG: Final decision action: {final_decision.get('action')}")
            if final_decision.get("action") == "CRITICAL_INTERVENTION":
                print("🚨 DEBUG: CRITICAL detected! Calling _send_alert...")
                self._send_alert(cascade_record)
            else:
                print(f"ℹ️ DEBUG: Decision is {final_decision.get('action')}, no alert needed")
            
            duration = cascade_record['duration']
            logger.info(f"Cascade completed in {duration:.2f}s")
            
            return {
                'success': True,
                'final_decision': final_decision,
                'water_alert': water_data.get('alert_level', 'NORMAL'),
                'water_svi': water_data.get('svi', 0),
                'immunity_status': immunity_result.get('immunity_status', 'UNKNOWN'),
                'immunity_score': immunity_result.get('immunity_score', 0),
                'pathogen_risk': pathogen_result.get('risk_level', 'unknown'),
                'module_c_data': module_c_data,
                'recommended_action': final_decision.get('action', 'MONITOR'),
                'confidence': final_decision.get('confidence', 0.0),
                'timestamp': cascade_record['timestamp'],
                'data_sources': cascade_record['data_sources'],
                'duration': duration
            }
            
        except Exception as e:
            logger.error(f"Cascade execution failed: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
        finally:
            self.running = False
    
    def _generate_decision(self, water_data: Dict, immunity_result: Dict) -> Dict:
        """Generate adaptive decision based on multi-factor analysis"""
        water_svi = water_data.get('svi', 0)
        water_quality = water_data.get('quality', 0)
        immunity_score = immunity_result.get('immunity_score', 0)
        
        if water_svi > 0.35 or water_quality < 60:
            action = 'CRITICAL_INTERVENTION'
            confidence = 0.85
        elif water_svi > 0.25 or water_quality < 75 or immunity_score < 0.6:
            action = 'MONITOR_CLOSELY'
            confidence = 0.85
        elif immunity_score > 0.8:
            action = 'NORMAL_OPERATIONS'
            confidence = 0.90
        else:
            action = 'PREVENTIVE_ACTION'
            confidence = 0.70
        
        print(f"   📊 Decision factors: SVI={water_svi:.3f}, Quality={water_quality}, Immunity={immunity_score:.3f}")
        
        return {
            'action': action,
            'confidence': confidence,
            'factors': {
                'water_svi': water_svi,
                'water_quality': water_quality,
                'soil_immunity': immunity_score,
                'water_alert': water_data.get('alert_level', 'NORMAL'),
                'immunity_status': immunity_result.get('immunity_status', 'UNKNOWN')
            },
            'timestamp': datetime.now().isoformat()
        }
    
    def _save_report(self, record: Dict) -> None:
        """Save cascade report to TXT format only - يكتب في reports/daily خارج src"""
        reports_dir = project_root / "reports"
        reports_dir.mkdir(exist_ok=True)
        
        # Create daily directory
        daily_dir = reports_dir / "daily"
        daily_dir.mkdir(exist_ok=True)
        
        # Save daily report (TXT فقط)
        now = datetime.now()
        daily_filename = daily_dir / f"report_{now.strftime('%Y-%m-%d')}.txt"
        
        # If file exists, append update
        if daily_filename.exists():
            with open(daily_filename, 'a', encoding='utf-8') as f:
                f.write(f'\n{"="*40}\n')
                f.write(f'🕒 Hourly Update: {now.strftime("%H:%M:%S")}\n')
                f.write(f'{"="*40}\n')
                f.write(f'🎯 Decision: {record.get("final_decision", {}).get("action", "UNKNOWN")}\n')
                f.write(f'💧 Water SVI: {record.get("water_data", {}).get("svi", 0):.3f}\n')
                f.write(f'🛡️ Immunity: {record.get("immunity_result", {}).get("immunity_score", 0):.3f}\n')
                f.write(f'📊 Confidence: {record.get("final_decision", {}).get("confidence", 0):.0%}\n')
                
                # Module C info
                module_c = record.get('module_c_data')
                if module_c:
                    f.write(f'🧬 Module C: {module_c.get("file", "unknown")}\n')
                    f.write(f'   Cycle: {module_c.get("cycle", 0)}\n')
                    f.write(f'   Dominant: {module_c.get("dominant", "UNKNOWN")}\n')
                    f.write(f'   Certainty: {module_c.get("certainty", 0):.0%}\n')
                
                f.write(f'{"="*40}\n')
            logger.info(f"Updated daily report: {daily_filename}")
        else:
            # Create new daily report
            with open(daily_filename, 'w', encoding='utf-8') as f:
                f.write('='*50 + '\n')
                f.write(f'BioShield Daily Report - {now.strftime("%Y-%m-%d")}\n')
                f.write('='*50 + '\n\n')
                f.write(f'📅 Date: {now.strftime("%Y-%m-%d")}\n')
                f.write(f'🕒 Generated: {now.strftime("%H:%M:%S")}\n')
                f.write(f'🚀 System: BioShield Cascade v{self.version}\n')
                f.write(f'🌐 Live Web: {"ENABLED" if self.use_live_web else "DISABLED"}\n')
                f.write('\n' + '-'*40 + '\n')
                f.write(f'🎯 First Decision: {record.get("final_decision", {}).get("action", "UNKNOWN")}\n')
                f.write(f'💧 Water SVI: {record.get("water_data", {}).get("svi", 0):.3f}\n')
                f.write(f'🛡️ Immunity: {record.get("immunity_result", {}).get("immunity_score", 0):.3f}\n')
                f.write(f'📊 Confidence: {record.get("final_decision", {}).get("confidence", 0):.0%}\n')
                
                # Module C info
                module_c = record.get('module_c_data')
                if module_c:
                    f.write(f'\n🧬 Module C Integration:\n')
                    f.write(f'   📄 Latest File: {module_c.get("file", "unknown")}\n')
                    f.write(f'   🔄 Cycle: {module_c.get("cycle", 0)}\n')
                    f.write(f'   🎯 Dominant Scenario: {module_c.get("dominant", "UNKNOWN")}\n')
                    f.write(f'   📈 Certainty: {module_c.get("certainty", 0):.0%}\n')
                    f.write(f'   📁 Location: {module_c.get("path", "N/A")}\n')
                
                f.write('\n' + '='*50 + '\n')
                f.write('Note: Module C JSON files remain in src/modules/pathogen_intel/core/json/daily/\n')
                f.write('='*50 + '\n')
            logger.info(f"Created daily report: {daily_filename}")
    
    def run_continuous_monitoring(self, interval: int = 300) -> None:
        """Run cascade continuously at specified interval"""
        print(f"🔁 Starting continuous monitoring (interval: {interval}s)")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                result = self.run_full_cascade()
                print(f"\n✅ Cascade completed at {result['timestamp']}")
                print(f"   Decision: {result['recommended_action']} (Confidence: {result['confidence']:.0%})")
                
                module_c = result.get('module_c_data')
                if module_c:
                    print(f"   📄 Module C: {module_c.get('file')} (Cycle {module_c.get('cycle')}, {module_c.get('dominant')} {module_c.get('certainty', 0):.0%})")
                
                print(f"⏳ Waiting {interval} seconds...\n")
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n🛑 Monitoring stopped by user")
        except Exception as e:
            print(f"❌ Monitoring error: {e}")


def main():
    """Main entry point"""
    print("🧪 Testing Cascade Manager...")
    
    current_dir = os.getcwd()
    print(f"📁 Current directory: {current_dir}")
    
    try:
        manager = CascadeManager(use_live_web=True)
        
        print("\n" + "="*50)
        print("Running single cascade execution...")
        print("="*50)
        
        result = manager.run_full_cascade()
        
        if result['success']:
            print(f"\n✅ SUCCESS!")
            print(f"🎯 Decision: {result['recommended_action']}")
            print(f"📊 Confidence: {result['confidence']:.0%}")
            print(f"💧 Water SVI: {result['water_svi']:.3f}")
            print(f"🛡️ Immunity: {result['immunity_score']:.3f}")
            
            if result.get('module_c_data'):
                print(f"📄 Module C: {result['module_c_data'].get('file', 'N/A')}")
                print(f"   Cycle: {result['module_c_data'].get('cycle', 0)}")
                print(f"   Dominant: {result['module_c_data'].get('dominant', 'UNKNOWN')}")
        else:
            print(f"\n❌ FAILED: {result['error']}")
            
    except Exception as e:
        print(f"❌ Error initializing CascadeManager: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
