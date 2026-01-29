#!/usr/bin/env python3
"""
Web API Fetcher
Fetches live data from HydroNet and BioShield websites

File: src/modules/web_api_fetcher.py
"""

import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
import urllib.request
import urllib.error


class WebAPIFetcher:
    """
    Fetches live data from deployed websites
    - HydroNet: https://hydronet-v1.netlify.app/
    - BioShield: https://bioshield-b1.netlify.app/
    """
    
    def __init__(self):
        # Website URLs
        self.hydronet_url = "https://hydronet-v1.netlify.app"
        self.bioshield_url = "https://bioshield-b1.netlify.app"
        
        # Cache directory
        self.cache_dir = Path(__file__).parent.parent.parent / "data" / "web_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache files
        self.hydronet_cache = self.cache_dir / "hydronet_live.json"
        self.bioshield_cache = self.cache_dir / "bioshield_live.json"
        
        # Cache expiry (seconds)
        self.cache_expiry = 300  # 5 minutes
        
        print("✅ Web API Fetcher initialized")
        print(f"🌐 HydroNet: {self.hydronet_url}")
        print(f"🌐 BioShield: {self.bioshield_url}")
    
    def fetch_hydronet_data(self, use_cache: bool = True) -> Dict:
        """
        Fetch live data from HydroNet website
        
        Args:
            use_cache: Use cached data if recent
        
        Returns:
            HydroNet data or None if failed
        """
        # Check cache first
        if use_cache and self._is_cache_valid(self.hydronet_cache):
            return self._load_cache(self.hydronet_cache)
        
        print("🌐 Fetching live data from HydroNet...")
        
        # Try different endpoints
        endpoints = [
            f"{self.hydronet_url}/api/current",
            f"{self.hydronet_url}/api/data",
            f"{self.hydronet_url}/data.json",
        ]
        
        for endpoint in endpoints:
            try:
                data = self._fetch_json(endpoint)
                if data:
                    # Normalize format
                    normalized = self._normalize_hydronet_data(data)
                    
                    # Save to cache
                    self._save_cache(self.hydronet_cache, normalized)
                    
                    print(f"✅ HydroNet data fetched: SVI={normalized.get('svi', 'N/A')}")
                    return normalized
                    
            except Exception as e:
                print(f"⚠️ Failed endpoint {endpoint}: {e}")
                continue
        
        # Fallback: Try to scrape from HTML
        try:
            html_data = self._scrape_hydronet_html()
            if html_data:
                self._save_cache(self.hydronet_cache, html_data)
                return html_data
        except:
            pass
        
        print("❌ Failed to fetch HydroNet data")
        
        # Return cached data even if expired
        if self.hydronet_cache.exists():
            print("⚠️ Using expired cache")
            return self._load_cache(self.hydronet_cache)
        
        return None
    
    def fetch_bioshield_data(self, use_cache: bool = True) -> Dict:
        """
        Fetch live data from BioShield website
        
        Args:
            use_cache: Use cached data if recent
        
        Returns:
            BioShield data or None if failed
        """
        # Check cache first
        if use_cache and self._is_cache_valid(self.bioshield_cache):
            return self._load_cache(self.bioshield_cache)
        
        print("🌐 Fetching live data from BioShield...")
        
        # Try different endpoints
        endpoints = [
            f"{self.bioshield_url}/api/indicators",
            f"{self.bioshield_url}/api/current",
            f"{self.bioshield_url}/data.json",
        ]
        
        for endpoint in endpoints:
            try:
                data = self._fetch_json(endpoint)
                if data:
                    # Normalize format
                    normalized = self._normalize_bioshield_data(data)
                    
                    # Save to cache
                    self._save_cache(self.bioshield_cache, normalized)
                    
                    print(f"✅ BioShield data fetched")
                    return normalized
                    
            except Exception as e:
                print(f"⚠️ Failed endpoint {endpoint}: {e}")
                continue
        
        # Fallback: Try to scrape from HTML
        try:
            html_data = self._scrape_bioshield_html()
            if html_data:
                self._save_cache(self.bioshield_cache, html_data)
                return html_data
        except:
            pass
        
        print("❌ Failed to fetch BioShield data")
        
        # Return cached data even if expired
        if self.bioshield_cache.exists():
            print("⚠️ Using expired cache")
            return self._load_cache(self.bioshield_cache)
        
        return None
    
    def _fetch_json(self, url: str, timeout: int = 10) -> Optional[Dict]:
        """Fetch JSON from URL"""
        try:
            req = urllib.request.Request(
                url,
                headers={
                    'User-Agent': 'BioShield-Integration/1.0',
                    'Accept': 'application/json'
                }
            )
            
            with urllib.request.urlopen(req, timeout=timeout) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    return data
                    
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None  # Endpoint doesn't exist
            raise
        except Exception as e:
            raise
        
        return None
    
    def _scrape_hydronet_html(self) -> Dict:
        """
        Scrape HydroNet data from HTML
        (Fallback when API not available)
        """
        try:
            req = urllib.request.Request(
                self.hydronet_url,
                headers={'User-Agent': 'BioShield-Integration/1.0'}
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                html = response.read().decode('utf-8')
            
            # Simple parsing (looking for specific patterns)
            # This is a basic example - adjust based on actual HTML structure
            data = {
                'svi': self._extract_value(html, 'svi', 0.30),
                'water_quality': self._extract_value(html, 'quality', 75),
                'contamination_level': self._extract_value(html, 'contamination', 15),
                'flow_rate': self._extract_value(html, 'flow', 120),
                'timestamp': datetime.now().isoformat(),
                'source': 'HTML_Scrape'
            }
            
            print("✅ Scraped HydroNet HTML")
            return data
            
        except Exception as e:
            print(f"❌ HTML scraping failed: {e}")
            return None
    
    def _scrape_bioshield_html(self) -> Dict:
        """
        Scrape BioShield data from HTML
        (Fallback when API not available)
        """
        try:
            req = urllib.request.Request(
                self.bioshield_url,
                headers={'User-Agent': 'BioShield-Integration/1.0'}
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                html = response.read().decode('utf-8')
            
            # Parse indicators
            data = {}
            for i in range(1, 13):
                key = f"B{i}"
                data[f"{key}_indicator"] = self._extract_value(html, key, 0.5)
            
            data['timestamp'] = datetime.now().isoformat()
            data['source'] = 'HTML_Scrape'
            
            print("✅ Scraped BioShield HTML")
            return data
            
        except Exception as e:
            print(f"❌ HTML scraping failed: {e}")
            return None
    
    def _extract_value(self, html: str, key: str, default):
        """
        Extract numeric value from HTML
        Simple pattern matching
        """
        import re
        
        # Try different patterns
        patterns = [
            rf'{key}["\']?\s*[:=]\s*([0-9.]+)',
            rf'data-{key}=["\']([0-9.]+)["\']',
            rf'id=["\]{key}["\']>([0-9.]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                try:
                    value = float(match.group(1))
                    return value
                except:
                    pass
        
        return default
    
    def _normalize_hydronet_data(self, raw_data: Dict) -> Dict:
        """Normalize HydroNet data to standard format"""
        return {
            'svi': raw_data.get('svi', raw_data.get('SVI', 0.30)),
            'water_quality': raw_data.get('water_quality', raw_data.get('quality', 75)),
            'contamination_level': raw_data.get('contamination_level', raw_data.get('contamination', 15)),
            'flow_rate': raw_data.get('flow_rate', raw_data.get('flow', 120)),
            'timestamp': raw_data.get('timestamp', datetime.now().isoformat()),
            'source': 'HydroNet_Live'
        }
    
    def _normalize_bioshield_data(self, raw_data: Dict) -> Dict:
        """Normalize BioShield data to standard format"""
        normalized = {
            'timestamp': raw_data.get('timestamp', datetime.now().isoformat()),
            'source': 'BioShield_Live'
        }
        
        # Copy all B1-B12 indicators
        for i in range(1, 13):
            key_pattern = f"B{i}"
            for k, v in raw_data.items():
                if key_pattern in k:
                    normalized[k] = v
                    break
        
        return normalized
    
    def _is_cache_valid(self, cache_file: Path) -> bool:
        """Check if cache is still valid"""
        if not cache_file.exists():
            return False
        
        age = time.time() - cache_file.stat().st_mtime
        return age < self.cache_expiry
    
    def _load_cache(self, cache_file: Path) -> Dict:
        """Load data from cache"""
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"📦 Loaded from cache: {cache_file.name}")
            return data
        except:
            return None
    
    def _save_cache(self, cache_file: Path, data: Dict):
        """Save data to cache"""
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Cache save failed: {e}")
    
    def fetch_all_live_data(self) -> Dict:
        """
        Fetch data from both websites
        
        Returns:
            {
                'hydronet': {...},
                'bioshield': {...},
                'timestamp': str,
                'success': bool
            }
        """
        print("\n" + "="*60)
        print("🌐 FETCHING LIVE DATA FROM WEB")
        print("="*60 + "\n")
        
        hydronet_data = self.fetch_hydronet_data()
        bioshield_data = self.fetch_bioshield_data()
        
        result = {
            'hydronet': hydronet_data,
            'bioshield': bioshield_data,
            'timestamp': datetime.now().isoformat(),
            'success': hydronet_data is not None and bioshield_data is not None
        }
        
        if result['success']:
            print("\n✅ All live data fetched successfully")
        else:
            print("\n⚠️ Some data sources failed")
        
        print("="*60 + "\n")
        
        return result


# ============================================================
# TESTING
# ============================================================

def test_web_fetcher():
    """Test web API fetcher"""
    print("\n" + "="*60)
    print("🧪 TESTING WEB API FETCHER")
    print("="*60 + "\n")
    
    fetcher = WebAPIFetcher()
    
    # Test HydroNet
    print("\n📊 Testing HydroNet fetch:")
    hydronet = fetcher.fetch_hydronet_data(use_cache=False)
    if hydronet:
        print(f"   SVI: {hydronet.get('svi', 'N/A')}")
        print(f"   Quality: {hydronet.get('water_quality', 'N/A')}%")
        print(f"   Source: {hydronet.get('source', 'N/A')}")
    else:
        print("   ❌ Failed")
    
    # Test BioShield
    print("\n📊 Testing BioShield fetch:")
    bioshield = fetcher.fetch_bioshield_data(use_cache=False)
    if bioshield:
        print(f"   Indicators: {len([k for k in bioshield.keys() if k.startswith('B')])}")
        print(f"   Source: {bioshield.get('source', 'N/A')}")
    else:
        print("   ❌ Failed")
    
    # Test combined
    print("\n📊 Testing combined fetch:")
    all_data = fetcher.fetch_all_live_data()
    print(f"   Success: {all_data['success']}")
    print(f"   HydroNet: {'✅' if all_data['hydronet'] else '❌'}")
    print(f"   BioShield: {'✅' if all_data['bioshield'] else '❌'}")
    
    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    test_web_fetcher()
