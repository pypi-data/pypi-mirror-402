#!/usr/bin/env python3
"""
Cascade Manager - Main orchestration for A→B→C→D flow
Uses LIVE WEB DATA from deployed websites
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
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, project_root)

# Now import module wrappers with absolute path
try:
    from src.modules.hydronet import HydroNetWrapper
    from src.modules.aquacrop import AquaCropWrapper
    from src.modules.agro_immunity import AgroImmunityWrapper
    from modules.pathogen_intel.core.cascade_interface import CascadeInterfaceC
except ImportError:
    # Fallback for direct execution
    from modules.hydronet import HydroNetWrapper
    from modules.aquacrop import AquaCropWrapper
    from modules.agro_immunity import AgroImmunityWrapper
    from modules.pathogen_intel.core.cascade_interface import CascadeInterfaceC

logger = logging.getLogger(__name__)


class CascadeManager:
    """Main orchestrator for BioShield cascade flow with LIVE WEB DATA"""
    
    def __init__(self, config_path: Optional[str] = None, use_live_web: bool = True):
        self.name = "BioShield_Orchestrator_Live"
        self.version = "4.0.0"
        self.use_live_web = use_live_web
        
        # Load configuration
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "config" / "integration_config.yaml"
        self.config = self._load_config(config_path)
        
        # Initialize module wrappers WITH LIVE WEB
        print(f"🚀 Initializing Cascade Manager with LIVE WEB: {use_live_web}")
        
        self.hydronet = HydroNetWrapper(use_live_web=self.use_live_web)
        self.aquacrop = AquaCropWrapper()
        self.agro_immunity = AgroImmunityWrapper(use_live_web=self.use_live_web)
        self.pathogen_intel = CascadeInterfaceC()
        
        # State tracking
        self.cascade_history = []
        self.last_run = None
        self.running = False
        
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
            return {}
    
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
                # إرسال Webhook
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
                # Fallback: Save to local file
                self._fallback_alert(record)
        else:
            print(f"ℹ️ DEBUG: Not CRITICAL (decision: {decision}), skipping alert")
    
    def _log_alert_locally(self, alert_data: Dict) -> None:
        """Log alert locally as backup - TXT format only"""
        alert_dir = Path("reports/alerts")
        alert_dir.mkdir(exist_ok=True, parents=True)
        
        # Create timestamp for filename
        alert_time = datetime.fromisoformat(alert_data['timestamp'].replace('Z', '+00:00'))
        filename = f"alert_{alert_time.strftime('%Y%m%d_%H%M')}.txt"
        alert_file = alert_dir / filename
        
        # Write to TXT file
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
        
        # Also append to alerts.log
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
        alert_dir = Path("reports/alerts")
        alert_dir.mkdir(exist_ok=True, parents=True)
        
        # Create fallback alert file
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
            
            # Step 4: Process with Pathogen Intelligence (C)
            print("🧬 Step 4: Processing with Pathogen Intelligence...")
            self.pathogen_intel.receive_from_b(immunity_result)
            pathogen_result = self.pathogen_intel.receive_from_b({})
            if pathogen_result:
                print(f"   📊 Pathogen Risk Level: {pathogen_result.get('risk_level', 'unknown')}")
            else:
                print("   ⚠️ No pathogen analysis available")
                pathogen_result = {"risk_level": "unknown", "risk_score": 0.0}
            
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
                'recommended_action': final_decision.get('action', 'MONITOR'),
                'confidence': final_decision.get('confidence', 0.0),
                'timestamp': cascade_record['timestamp'],
                'data_sources': cascade_record['data_sources'],
                'duration': duration
            }
            
        except Exception as e:
            logger.error(f"Cascade execution failed: {e}")
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
        
        # Calculate decision based on thresholds
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
        """Save cascade report to file - TXT format only"""
        reports_dir = Path(self.config.get('paths', {}).get('reports', 'reports'))
        reports_dir.mkdir(exist_ok=True)
        
        # Create hourly directory for hourly reports
        hourly_dir = reports_dir / "hourly"
        hourly_dir.mkdir(exist_ok=True)
        
        # Create daily directory for daily reports
        daily_dir = reports_dir / "daily"
        daily_dir.mkdir(exist_ok=True)
        
        # Save hourly report (TXT)
        now = datetime.now()
        hourly_filename = hourly_dir / f"hourly_{now.strftime('%Y%m%d_%H%M')}.txt"
        
        with open(hourly_filename, 'w', encoding='utf-8') as f:
            f.write('='*50 + '\n')
            f.write('BioShield Hourly Report\n')
            f.write('='*50 + '\n\n')
            f.write(f'Time: {now.strftime("%Y-%m-%d %H:%M:%S")}\n')
            f.write(f'Decision: {record.get("final_decision", {}).get("action", "UNKNOWN")}\n')
            f.write(f'Water SVI: {record.get("water_data", {}).get("svi", 0):.3f}\n')
            f.write(f'Immunity Score: {record.get("immunity_result", {}).get("immunity_score", 0):.3f}\n')
            f.write(f'Confidence: {record.get("final_decision", {}).get("confidence", 0):.0%}\n')
            f.write(f'Duration: {record.get("duration", 0):.2f}s\n')
            f.write('\n' + '='*50)
        
        logger.info(f"Hourly report saved to {hourly_filename}")
        
        # Update daily report
        daily_filename = daily_dir / f"report_{now.strftime('%Y-%m-%d')}.txt"
        
        # If file exists, append update
        if daily_filename.exists():
            with open(daily_filename, 'a', encoding='utf-8') as f:
                f.write(f'\n=== Hourly Update ===\n')
                f.write(f'Time: {record["timestamp"][:19]}\n')
                f.write(f'Decision: {record.get("final_decision", {}).get("action", "UNKNOWN")}\n')
                f.write(f'SVI: {record.get("water_data", {}).get("svi", 0):.3f}\n')
                f.write('='*40 + '\n')
            logger.info(f"Updated daily report: {daily_filename}")
        else:
            # If file doesn't exist, create it
            with open(daily_filename, 'w', encoding='utf-8') as f:
                f.write('='*50 + '\n')
                f.write(f'BioShield Daily Report - {now.strftime("%Y-%m-%d")}\n')
                f.write('='*50 + '\n\n')
                f.write(f'🕒 Generated: {now.strftime("%Y-%m-%d %H:%M:%S")}\n')
                f.write(f'🎯 Decision: {record.get("final_decision", {}).get("action", "UNKNOWN")}\n')
                f.write(f'💧 Water SVI: {record.get("water_data", {}).get("svi", 0):.3f}\n')
                f.write(f'🛡️ Immunity: {record.get("immunity_result", {}).get("immunity_score", 0):.3f}\n')
                f.write(f'📊 Confidence: {record.get("final_decision", {}).get("confidence", 0):.0%}\n')
                f.write('\n' + '='*50)
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
                
                if result['success']:
                    print(f"   Water SVI: {result['water_svi']:.3f} (Alert: {result['water_alert']})")
                    print(f"   Immunity Score: {result['immunity_score']:.3f}")
                    print(f"   Pathogen Risk: {result.get('pathogen_risk', 'unknown')}")
                    print(f"   Data Sources: Hydro={result['data_sources']['hydro_source']}, Agro={result['data_sources']['agro_source']}")
                    
                    if result['recommended_action'] == 'CRITICAL_INTERVENTION':
                        print("   🚨 CRITICAL ALERT WAS SENT!")
                
                print(f"⏳ Waiting {interval} seconds...\n")
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n🛑 Monitoring stopped by user")
    
    def get_cascade_stats(self) -> Dict:
        """Get cascade execution statistics"""
        return {
            'total_runs': len(self.cascade_history),
            'last_run': self.last_run.isoformat() if self.last_run else None,
            'success_rate': self._calculate_success_rate(),
            'avg_duration': self._calculate_avg_duration(),
            'recent_alerts': self._get_recent_alerts(),
            'current_status': 'RUNNING' if self.running else 'IDLE',
            'live_web_enabled': self.use_live_web
        }
    
    def _calculate_success_rate(self) -> float:
        """Calculate success rate from history"""
        if not self.cascade_history:
            return 0.0
        
        successful = sum(1 for r in self.cascade_history if 'success' not in r or r.get('success', True))
        return successful / len(self.cascade_history)
    
    def _calculate_avg_duration(self) -> float:
        """Calculate average cascade duration"""
        if not self.cascade_history:
            return 0.0
        
        durations = [r.get('duration', 0) for r in self.cascade_history[-10:]]
        return sum(durations) / len(durations)
    
    def _get_recent_alerts(self) -> Dict:
        """Get recent alert statistics"""
        if not self.cascade_history:
            return {'critical': 0, 'warning': 0, 'normal': 0}
        
        alerts = {'critical': 0, 'warning': 0, 'normal': 0}
        for record in self.cascade_history[-10:]:
            water_data = record.get('water_data', {})
            alert = water_data.get('alert_level', 'normal').lower()
            if alert in alerts:
                alerts[alert] += 1
        
        return alerts


def main():
    """Main entry point for CLI"""
    import argparse
    
    parser = argparse.ArgumentParser(description="BioShield Cascade Manager with LIVE WEB")
    parser.add_argument('--mode', choices=['single', 'continuous', 'stats'], 
                       default='single', help='Operation mode')
    parser.add_argument('--interval', type=int, default=300,
                       help='Interval for continuous mode (seconds)')
    parser.add_argument('--config', type=str,
                       help='Path to configuration file')
    parser.add_argument('--live-web', action='store_true', default=True,
                       help='Use live web data (default: True)')
    parser.add_argument('--no-live-web', action='store_false', dest='live_web',
                       help='Disable live web data')
    
    args = parser.parse_args()
    
    # Initialize manager
    manager = CascadeManager(args.config, use_live_web=args.live_web)
    
    if args.mode == 'single':
        print(f"🚀 Running single cascade execution (Live Web: {args.live_web})...")
        result = manager.run_full_cascade()
        
        if result['success']:
            print(f"\n✅ Cascade completed successfully")
            print(f"📊 Results:")
            print(f"   Final Decision: {result['recommended_action']}")
            print(f"   Water SVI: {result['water_svi']:.3f} (Alert: {result['water_alert']})")
            print(f"   Immunity Score: {result['immunity_score']:.3f}")
            print(f"   Pathogen Risk: {result.get('pathogen_risk', 'unknown')}")
            print(f"   Confidence: {result['confidence']:.0%}")
            print(f"   Duration: {result.get('duration', 0):.2f}s")
            print(f"   Data Sources: Hydro={result['data_sources']['hydro_source']}, Agro={result['data_sources']['agro_source']}")
            
            if result['recommended_action'] == 'CRITICAL_INTERVENTION':
                print(f"\n🚨 CRITICAL ALERT SENT to Pipedream Webhook!")
                print(f"   ✅ Check Pipedream: https://eoi3vhd0zol7y5o.m.pipedream.net")
                print(f"   ✅ Local backup: reports/alerts/")
        else:
            print(f"❌ Cascade failed: {result['error']}")
            
    elif args.mode == 'continuous':
        manager.run_continuous_monitoring(args.interval)
        
    elif args.mode == 'stats':
        stats = manager.get_cascade_stats()
        print("📊 Cascade Statistics:")
        print(f"   Total Runs: {stats['total_runs']}")
        print(f"   Last Run: {stats['last_run']}")
        print(f"   Success Rate: {stats['success_rate']:.0%}")
        print(f"   Average Duration: {stats['avg_duration']:.2f}s")
        print(f"   Current Status: {stats['current_status']}")
        print(f"   Live Web: {'ENABLED' if stats['live_web_enabled'] else 'DISABLED'}")
        
        print("\n🔔 Recent Alerts:")
        for alert_type, count in stats['recent_alerts'].items():
            print(f"   {alert_type.upper()}: {count}")


if __name__ == "__main__":
    main()
