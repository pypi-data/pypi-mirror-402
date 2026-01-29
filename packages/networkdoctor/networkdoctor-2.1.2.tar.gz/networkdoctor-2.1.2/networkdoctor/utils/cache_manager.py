"""
Result Caching for NetworkDoctor
"""
import json
import hashlib
from typing import Any, Optional, Dict
from pathlib import Path
from datetime import datetime, timedelta
import time


class CacheManager:
    """Manages caching of scan results"""
    
    def __init__(self, cache_dir: str = ".networkdoctor_cache", ttl: int = 3600):
        """
        Initialize cache manager.
        
        Args:
            cache_dir: Cache directory path
            ttl: Time to live in seconds (default 1 hour)
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.ttl = ttl
    
    def _get_cache_key(self, target: str, doctor: str) -> str:
        """
        Generate cache key for target and doctor.
        
        Args:
            target: Target string
            doctor: Doctor module name
            
        Returns:
            Cache key (filename)
        """
        key_string = f"{target}:{doctor}"
        key_hash = hashlib.md5(key_string.encode()).hexdigest()
        return f"{key_hash}.json"
    
    def _get_cache_path(self, key: str) -> Path:
        """
        Get full cache file path.
        
        Args:
            key: Cache key
            
        Returns:
            Path to cache file
        """
        return self.cache_dir / key
    
    def get(self, target: str, doctor: str) -> Optional[Dict[str, Any]]:
        """
        Get cached result.
        
        Args:
            target: Target string
            doctor: Doctor module name
            
        Returns:
            Cached data or None
        """
        key = self._get_cache_key(target, doctor)
        cache_path = self._get_cache_path(key)
        
        if not cache_path.exists():
            return None
        
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Check TTL
            cached_time = datetime.fromisoformat(data.get("timestamp", ""))
            if datetime.now() - cached_time > timedelta(seconds=self.ttl):
                cache_path.unlink()  # Delete expired cache
                return None
            
            return data.get("result")
        except Exception:
            return None
    
    def set(self, target: str, doctor: str, result: Dict[str, Any]):
        """
        Cache a result.
        
        Args:
            target: Target string
            doctor: Doctor module name
            result: Result to cache
        """
        key = self._get_cache_key(target, doctor)
        cache_path = self._get_cache_path(key)
        
        try:
            data = {
                "timestamp": datetime.now().isoformat(),
                "target": target,
                "doctor": doctor,
                "result": result,
            }
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass  # Fail silently
    
    def clear(self, target: Optional[str] = None):
        """
        Clear cache.
        
        Args:
            target: Optional target to clear (None = clear all)
        """
        if target:
            # Clear specific target
            for cache_file in self.cache_dir.glob("*.json"):
                try:
                    with open(cache_file, "r") as f:
                        data = json.load(f)
                        if data.get("target") == target:
                            cache_file.unlink()
                except Exception:
                    pass
        else:
            # Clear all
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
    
    def cleanup_expired(self):
        """Remove expired cache entries"""
        now = datetime.now()
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                with open(cache_file, "r") as f:
                    data = json.load(f)
                    cached_time = datetime.fromisoformat(data.get("timestamp", ""))
                    if now - cached_time > timedelta(seconds=self.ttl):
                        cache_file.unlink()
            except Exception:
                cache_file.unlink()  # Delete corrupted cache







