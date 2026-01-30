#!/usr/bin/env python3
"""
HydroNet Wrapper - Water Intelligence System
Level A of BioShield Framework

Updated to support live web data from https://hydronet-v1.netlify.app/
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import urllib.request
import urllib.error

logger = logging.getLogger(__name__)


class HydroNetWrapper:
    """Wrapper for HydroNet water intelligence system (Level A)"""
    
    def __init__(self, config_path: Optional[str] = None, use_live_web: bool = True):
        self.name = "A_HydroNet"
        self.version = "1.0.0"
        self.path = "/storage/emulated/0/download/A_HydroNet"
        self.active = True
        
        # Web API configuration
        self.use_live_web = use_live_web
        self.web_url = "https://hydronet-v1.netlify.app"
        
        # Cache configuration
        self.cache_dir = Path(__file__).parent.parent.parent / "data" / "web_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / "hydronet_live.json"
        self.cache_expiry = 300  # 5 minutes
        
        logger.info(f"HydroNet wrapper initialized")
        logger.info(f"📁 Path: {self.path}")
        logger.info(f"🌐 Live Web: {'Enabled' if use_live_web else 'Disabled'}")
        if use_live_web:
            logger.info(f"🌐 URL: {self.web_url}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get module status"""
        return {
            "module": "hydronet",
            "status": "active", 
            "version": self.version,
            "path": self.path,
            "live_web": self.use_live_web,
            "web_url": self.web_url if self.use_live_web else None
        }
    
    def get_current_state(self) -> Dict[str, Any]:
        """
        Get current water analysis data
        Priority: Live Web → Cache → Local → Simulated
        """
        # Try live web data first
        if self.use_live_web:
            live_data = self._fetch_live_web_data()
            if live_data:
                logger.info("✅ Using live web data")
                return live_data
        
        # Try cache
        cache_data = self._load_cache()
        if cache_data:
            logger.info("📦 Using cached data")
            return cache_data
        
        # Try local files
        local_data = self._load_local_data()
        if local_data:
            logger.info("📁 Using local data")
            return local_data
        
        # Fallback to simulated
        logger.warning("⚠️ Using simulated data")
        return self._get_simulated_data()
    
    def _fetch_live_web_data(self) -> Optional[Dict[str, Any]]:
        """Fetch live data from HydroNet website"""
        endpoints = [
            f"{self.web_url}/api/current",
            f"{self.web_url}/api/data",
            f"{self.web_url}/data.json",
        ]
        
        for endpoint in endpoints:
            try:
                logger.debug(f"🌐 Trying endpoint: {endpoint}")
                
                req = urllib.request.Request(
                    endpoint,
                    headers={
                        'User-Agent': 'BioShield-Integration/1.0',
                        'Accept': 'application/json'
                    }
                )
                
                with urllib.request.urlopen(req, timeout=10) as response:
                    if response.status == 200:
                        raw_data = json.loads(response.read().decode('utf-8'))
                        
                        # Normalize and save to cache
                        normalized = self._normalize_web_data(raw_data)
                        self._save_cache(normalized)
                        
                        logger.info(f"✅ Fetched from: {endpoint}")
                        return normalized
                        
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    continue  # Try next endpoint
                logger.debug(f"HTTP Error {e.code}: {endpoint}")
            except Exception as e:
                logger.debug(f"Error fetching {endpoint}: {e}")
                continue
        
        # If API fails, try HTML scraping
        try:
            return self._scrape_html()
        except:
            pass
        
        return None
    
    def _scrape_html(self) -> Optional[Dict[str, Any]]:
        """Scrape data from HTML (fallback)"""
        try:
            req = urllib.request.Request(
                self.web_url,
                headers={'User-Agent': 'BioShield-Integration/1.0'}
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                html = response.read().decode('utf-8')
            
            import re
            
            # Extract values using regex
            svi = self._extract_number(html, r'svi["\']?\s*[:=]\s*([0-9.]+)', 0.30)
            quality = self._extract_number(html, r'quality["\']?\s*[:=]\s*([0-9.]+)', 75)
            contamination = self._extract_number(html, r'contamination["\']?\s*[:=]\s*([0-9.]+)', 15)
            flow = self._extract_number(html, r'flow["\']?\s*[:=]\s*([0-9.]+)', 120)
            
            data = {
                "timestamp": datetime.now().isoformat(),
                "svi": svi,
                "quality": int(quality),
                "contamination": contamination,
                "flow": int(flow),
                "alert_level": self._calculate_alert_level(svi, quality, contamination),
                "source": "web_scrape",
                "predictions": {
                    "current_svi": svi,
                    "predicted_svi": min(svi * 1.15, 0.5),
                    "trend": "increasing" if svi > 0.35 else "stable",
                    "confidence": 0.65
                }
            }
            
            self._save_cache(data)
            logger.info("✅ Scraped data from HTML")
            return data
            
        except Exception as e:
            logger.debug(f"HTML scraping failed: {e}")
            return None
    
    def _extract_number(self, text: str, pattern: str, default: float) -> float:
        """Extract number from text using regex"""
        import re
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1))
            except:
                pass
        return default
    
    def _normalize_web_data(self, raw_data: Dict) -> Dict[str, Any]:
        """Normalize web data to standard format"""
        svi = raw_data.get('svi', raw_data.get('SVI', 0.30))
        quality = raw_data.get('water_quality', raw_data.get('quality', 75))
        contamination = raw_data.get('contamination_level', raw_data.get('contamination', 15))
        flow = raw_data.get('flow_rate', raw_data.get('flow', 120))
        
        return {
            "timestamp": raw_data.get('timestamp', datetime.now().isoformat()),
            "svi": float(svi),
            "quality": int(quality),
            "contamination": float(contamination),
            "flow": int(flow),
            "alert_level": self._calculate_alert_level(svi, quality, contamination),
            "source": "web_live",
            "predictions": raw_data.get('predictions', {
                "current_svi": float(svi),
                "predicted_svi": min(float(svi) * 1.15, 0.5),
                "trend": "increasing" if float(svi) > 0.35 else "stable",
                "confidence": 0.75
            })
        }
    
    def _calculate_alert_level(self, svi: float, quality: float, contamination: float) -> str:
        """Calculate alert level based on thresholds"""
        if svi > 0.35 or quality < 60 or contamination > 30:
            return "CRITICAL"
        elif svi > 0.25 or quality < 75 or contamination > 20:
            return "WARNING"
        else:
            return "NORMAL"
    
    def _load_cache(self) -> Optional[Dict[str, Any]]:
        """Load data from cache if valid"""
        if not self.cache_file.exists():
            return None
        
        try:
            # Check cache age
            import time
            age = time.time() - self.cache_file.stat().st_mtime
            
            if age > self.cache_expiry:
                logger.debug("Cache expired")
                return None
            
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            logger.debug(f"Loaded from cache (age: {age:.0f}s)")
            return data
            
        except Exception as e:
            logger.debug(f"Cache load failed: {e}")
            return None
    
    def _save_cache(self, data: Dict[str, Any]):
        """Save data to cache"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.debug("Data cached successfully")
        except Exception as e:
            logger.debug(f"Cache save failed: {e}")
    
    def _load_local_data(self) -> Optional[Dict[str, Any]]:
        """Load data from local files"""
        local_file = Path(self.path) / "exports" / "current_state.json"
        
        if local_file.exists():
            try:
                with open(local_file, 'r', encoding='utf-8') as f:
                    raw_data = json.load(f)
                return self._normalize_web_data(raw_data)
            except Exception as e:
                logger.debug(f"Local data load failed: {e}")
        
        return None
    
    def _get_simulated_data(self) -> Dict[str, Any]:
        """Generate simulated data (last resort fallback)"""
        import random
        
        svi = round(random.uniform(0.25, 0.40), 3)
        quality = random.randint(60, 85)
        contamination = round(random.uniform(15, 30), 1)
        flow = random.randint(90, 130)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "svi": svi,
            "quality": quality,
            "contamination": contamination,
            "flow": flow,
            "alert_level": self._calculate_alert_level(svi, quality, contamination),
            "source": "simulated",
            "predictions": {
                "current_svi": svi,
                "predicted_svi": min(svi * 1.15, 0.5),
                "trend": "increasing" if svi > 0.35 else "stable",
                "confidence": 0.50
            }
        }
    
    def export_for_integration(self) -> Dict[str, Any]:
        """Export data for BioShield integration"""
        state = self.get_current_state()
        return {
            "system": "HydroNet",
            "level": "A",
            "timestamp": datetime.now().isoformat(),
            "data": state,
            "ready": True,
            "data_source": state.get("source", "unknown")
        }
    
    def get_predictions(self, months_ahead: int = 8) -> Dict[str, Any]:
        """Get water system predictions"""
        state = self.get_current_state()
        predictions = state.get("predictions", {})
        
        return {
            "current_svi": predictions.get("current_svi", state["svi"]),
            "predicted_svi_8m": predictions.get("predicted_svi", state["svi"] * 1.15),
            "trend": predictions.get("trend", "stable"),
            "confidence": predictions.get("confidence", 0.75),
            "months_ahead": months_ahead,
            "timestamp": datetime.now().isoformat()
        }
    
    def clear_cache(self):
        """Clear cached data"""
        if self.cache_file.exists():
            self.cache_file.unlink()
            logger.info("Cache cleared")


# ============================================================
# TESTING
# ============================================================


def get_hydronet_data(): 
    """ 
    Get HydroNet data in standard format for integration 
    """ 
    wrapper = HydroNetWrapper(use_live_web=True) 
    return wrapper.get_current_state() 

def test_hydronet_wrapper():
    """Test HydroNet wrapper with live web data"""
    print("\n" + "="*60)
    print("🧪 TESTING HYDRONET WRAPPER (WITH LIVE WEB)")
    print("="*60 + "\n")
    
    # Test with live web enabled
    print("📊 Test 1: With Live Web Data")
    wrapper_web = HydroNetWrapper(use_live_web=True)
    
    state = wrapper_web.get_current_state()
    print(f"   SVI: {state['svi']:.3f}")
    print(f"   Quality: {state['quality']}%")
    print(f"   Contamination: {state['contamination']:.1f}")
    print(f"   Alert Level: {state['alert_level']}")
    print(f"   Data Source: {state['source']}")
    
    # Test predictions
    print("\n📊 Test 2: Predictions")
    predictions = wrapper_web.get_predictions()
    print(f"   Current SVI: {predictions['current_svi']:.3f}")
    print(f"   Predicted SVI (8m): {predictions['predicted_svi_8m']:.3f}")
    print(f"   Trend: {predictions['trend']}")
    print(f"   Confidence: {predictions['confidence']*100:.0f}%")
    
    # Test export
    print("\n📊 Test 3: Export for Integration")
    export = wrapper_web.export_for_integration()
    print(f"   System: {export['system']}")
    print(f"   Level: {export['level']}")
    print(f"   Ready: {export['ready']}")
    print(f"   Data Source: {export['data_source']}")
    
    # Test without web (fallback)
    print("\n📊 Test 4: Without Live Web (Fallback)")
    wrapper_local = HydroNetWrapper(use_live_web=False)
    state_local = wrapper_local.get_current_state()
    print(f"   Data Source: {state_local['source']}")
    
    # Test status
    print("\n📊 Test 5: Status")
    status = wrapper_web.get_status()
    for key, value in status.items():
        print(f"   {key}: {value}")
    
    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s - %(message)s'
    )
    
    test_hydronet_wrapper()