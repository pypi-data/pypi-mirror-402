#!/usr/bin/env python3
"""
Agro Immunity Wrapper - Agricultural Defense System
Level B of BioShield Framework

Updated to support live web data from https://bioshield-b1.netlify.app/
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import urllib.request
import urllib.error

logger = logging.getLogger(__name__)


class AgroImmunityWrapper:
    """Wrapper for Agro_Immunity system (Level B)"""
    
    def __init__(self, config_path: Optional[str] = None, use_live_web: bool = True):
        self.name = "B_Agro_Immunity"
        self.version = "1.0.0"
        self.path = "/storage/emulated/0/download/B_Agro_Immunity"
        self.active = True
        
        # Web API configuration
        self.use_live_web = use_live_web
        self.web_url = "https://bioshield-b1.netlify.app"
        
        # Cache configuration
        self.cache_dir = Path(__file__).parent.parent.parent / "data" / "web_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / "bioshield_live.json"
        self.cache_expiry = 300  # 5 minutes
        
        logger.info(f"Agro-Immunity wrapper initialized")
        logger.info(f"📁 Path: {self.path}")
        logger.info(f"🌐 Live Web: {'Enabled' if use_live_web else 'Disabled'}")
        if use_live_web:
            logger.info(f"🌐 URL: {self.web_url}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get module status"""
        return {
            "module": "agro_immunity",
            "status": "active",
            "version": self.version,
            "path": self.path,
            "live_web": self.use_live_web,
            "web_url": self.web_url if self.use_live_web else None
        }
    
    def get_immunity_strength(self) -> Dict[str, Any]:
        """
        Get current immunity strength assessment
        Priority: Live Web → Cache → Local → Simulated
        """
        # Try live web data first
        if self.use_live_web:
            live_data = self._fetch_live_web_data()
            if live_data:
                logger.info("✅ Using live web data")
                return self._normalize_web_data(live_data)
        
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
        """Fetch live data from BioShield website"""
        endpoints = [
            f"{self.web_url}/api/indicators",
            f"{self.web_url}/api/current",
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
                        self._save_cache(raw_data)
                        logger.info(f"✅ Fetched from: {endpoint}")
                        return raw_data
                        
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
            
            # Extract B1-B12 indicators
            data = {"timestamp": datetime.now().isoformat()}
            
            for i in range(1, 13):
                key = f"B{i}"
                # استخدام raw string مع r'' للتخلص من مشكلة escape sequences
                pattern = rf'{key}["\']?\s*[:=]\s*([0-9.]+)'
                value = self._extract_number(html, pattern, 0.5)
                data[f"{key}_indicator"] = value
            
            # Extract overall immunity
            immunity = self._extract_number(html, r'immunity["\']?\s*[:=]\s*([0-9.]+)', 0.7)
            data["immunity_score"] = immunity
            
            data["source"] = "web_scrape"
            
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
        # Extract B1-B12 indicators
        indicators = {}
        for i in range(1, 13):
            key = f"B{i}"
            for k, v in raw_data.items():
                if key in k:
                    indicators[k] = v
                    break
        
        immunity = raw_data.get('immunity_score', raw_data.get('immunity', 0.7))
        
        return {
            "timestamp": raw_data.get('timestamp', datetime.now().isoformat()),
            "immunity_score": float(immunity),
            "immunity_status": self._get_immunity_status(float(immunity)),
            "indicators": indicators,
            "source": "web_live",
            "components": {
                "soil_health": indicators.get('B1_indicator', 0.6),
                "nutrient_centrality": indicators.get('B2_indicator', 0.65),
                "microbial_connect": indicators.get('B3_indicator', 0.7),
                "hydro_agro_sync": indicators.get('B4_indicator', 0.33),
                "genetic_purity": indicators.get('B7_indicator', 0.8),
                "pathogen_resistance": indicators.get('B8_indicator', 0.75),
                "adaptive_diversity": indicators.get('B9_indicator', 0.7),
                "pollinator_connectivity": indicators.get('B10_indicator', 0.4)
            }
        }
    
    def _get_immunity_status(self, score: float) -> str:
        """Get immunity status based on score"""
        if score > 0.8:
            return "VERY_STRONG"
        elif score > 0.7:
            return "STRONG"
        elif score > 0.6:
            return "MODERATE"
        elif score > 0.5:
            return "WEAK"
        else:
            return "CRITICAL"
    
    def _load_cache(self) -> Optional[Dict[str, Any]]:
        """Load data from cache if valid"""
        if not self.cache_file.exists():
            return None
        
        try:
            import time
            age = time.time() - self.cache_file.stat().st_mtime
            
            if age > self.cache_expiry:
                logger.debug("Cache expired")
                return None
            
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            logger.debug(f"Loaded from cache (age: {age:.0f}s)")
            return self._normalize_web_data(data)
            
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
        local_file = Path(self.path) / "exports" / "soil_data.json"
        
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
        
        # Generate B1-B12 indicators
        indicators = {}
        for i in range(1, 13):
            indicators[f"B{i}_indicator"] = round(random.uniform(0.4, 0.9), 3)
        
        immunity_score = round(random.uniform(0.6, 0.85), 3)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "immunity_score": immunity_score,
            "immunity_status": self._get_immunity_status(immunity_score),
            "indicators": indicators,
            "source": "simulated",
            "components": {
                "soil_health": indicators.get('B1_indicator', 0.6),
                "nutrient_centrality": indicators.get('B2_indicator', 0.65),
                "microbial_connect": indicators.get('B3_indicator', 0.7),
                "hydro_agro_sync": indicators.get('B4_indicator', 0.33),
                "genetic_purity": indicators.get('B7_indicator', 0.8),
                "pathogen_resistance": indicators.get('B8_indicator', 0.75),
                "adaptive_diversity": indicators.get('B9_indicator', 0.7),
                "pollinator_connectivity": indicators.get('B10_indicator', 0.4)
            }
        }
    
    def receive_a_data(self, transformed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Receive and process data from A via AquaCrop"""
        alert = transformed_data.get("alert_level", "NORMAL")
        
        return {
            "timestamp": datetime.now().isoformat(),
            "received_from": "AquaCrop_Bridge",
            "alert_level": alert,
            "processing": "success",
            "next_step": "C_Pathogen_Intel"
        }
    
    def export_for_integration(self) -> Dict[str, Any]:
        """Export data for BioShield integration"""
        state = self.get_immunity_strength()
        return {
            "system": "Agro_Immunity",
            "level": "B",
            "timestamp": datetime.now().isoformat(),
            "data": state,
            "ready": True,
            "data_source": state.get("source", "unknown")
        }
    
    def clear_cache(self):
        """Clear cached data"""
        if self.cache_file.exists():
            self.cache_file.unlink()
            logger.info("Cache cleared")


# ============================================================
# TESTING
# ============================================================

def test_agro_immunity_wrapper():
    """Test Agro Immunity wrapper with live web data"""
    print("\n" + "="*60)
    print("🧪 TESTING AGRO IMMUNITY WRAPPER (WITH LIVE WEB)")
    print("="*60 + "\n")
    
    # Test with live web enabled
    print("📊 Test 1: With Live Web Data")
    wrapper_web = AgroImmunityWrapper(use_live_web=True)
    
    immunity = wrapper_web.get_immunity_strength()
    print(f"   Immunity Score: {immunity['immunity_score']:.3f}")
    print(f"   Immunity Status: {immunity['immunity_status']}")
    print(f"   Indicators: {len(immunity['indicators'])}")
    print(f"   Data Source: {immunity['source']}")
    
    # Test export
    print("\n📊 Test 2: Export for Integration")
    export = wrapper_web.export_for_integration()
    print(f"   System: {export['system']}")
    print(f"   Level: {export['level']}")
    print(f"   Ready: {export['ready']}")
    print(f"   Data Source: {export['data_source']}")
    
    # Test without web (fallback)
    print("\n📊 Test 3: Without Live Web (Fallback)")
    wrapper_local = AgroImmunityWrapper(use_live_web=False)
    immunity_local = wrapper_local.get_immunity_strength()
    print(f"   Data Source: {immunity_local['source']}")
    
    # Test status
    print("\n📊 Test 4: Status")
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
    
    test_agro_immunity_wrapper()
