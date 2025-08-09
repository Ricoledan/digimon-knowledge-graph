import json
import hashlib
from pathlib import Path
from typing import Any, Dict, Optional, Union
from datetime import datetime, timedelta

from loguru import logger


class Cache:
    """Simple file-based cache for storing scraped data and translations."""
    
    def __init__(self, cache_dir: Union[str, Path], ttl_hours: int = 24):
        """Initialize cache with directory and time-to-live."""
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl = timedelta(hours=ttl_hours)
        self._metadata_file = self.cache_dir / "_metadata.json"
        self._metadata = self._load_metadata()
        
    def _load_metadata(self) -> Dict[str, Any]:
        """Load cache metadata."""
        if self._metadata_file.exists():
            with open(self._metadata_file, 'r') as f:
                return json.load(f)
        return {}
        
    def _save_metadata(self) -> None:
        """Save cache metadata."""
        with open(self._metadata_file, 'w') as f:
            json.dump(self._metadata, f, indent=2)
            
    def _get_cache_key(self, key: str) -> str:
        """Generate a safe filename from cache key."""
        # Use SHA256 hash for consistent filenames
        hash_obj = hashlib.sha256(key.encode())
        return hash_obj.hexdigest()[:16]
        
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if it exists and hasn't expired."""
        cache_key = self._get_cache_key(key)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if not cache_file.exists():
            return None
            
        # Check if expired
        metadata = self._metadata.get(cache_key, {})
        if metadata:
            cached_time = datetime.fromisoformat(metadata.get("timestamp", ""))
            if datetime.now() - cached_time > self.ttl:
                logger.debug(f"Cache expired for key: {key}")
                self.delete(key)
                return None
                
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.debug(f"Cache hit for key: {key}")
                return data.get("value")
        except Exception as e:
            logger.error(f"Error reading cache for key {key}: {e}")
            return None
            
    def set(self, key: str, value: Any) -> None:
        """Set value in cache."""
        cache_key = self._get_cache_key(key)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        try:
            data = {
                "key": key,
                "value": value,
                "timestamp": datetime.now().isoformat()
            }
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            # Update metadata
            self._metadata[cache_key] = {
                "original_key": key,
                "timestamp": data["timestamp"]
            }
            self._save_metadata()
            
            logger.debug(f"Cached value for key: {key}")
        except Exception as e:
            logger.error(f"Error caching value for key {key}: {e}")
            
    def delete(self, key: str) -> None:
        """Delete value from cache."""
        cache_key = self._get_cache_key(key)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if cache_file.exists():
            cache_file.unlink()
            
        if cache_key in self._metadata:
            del self._metadata[cache_key]
            self._save_metadata()
            
    def clear(self) -> None:
        """Clear all cached values."""
        for cache_file in self.cache_dir.glob("*.json"):
            if cache_file.name != "_metadata.json":
                cache_file.unlink()
                
        self._metadata = {}
        self._save_metadata()
        logger.info("Cache cleared")
        
    def size(self) -> int:
        """Get number of items in cache."""
        return len(list(self.cache_dir.glob("*.json"))) - 1  # Exclude metadata
        

class TranslationCache(Cache):
    """Specialized cache for translations."""
    
    def __init__(self, cache_file: Union[str, Path]):
        """Initialize translation cache with a single file."""
        self.cache_file = Path(cache_file)
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        self._cache: Dict[str, str] = self._load_cache()
        
    def _load_cache(self) -> Dict[str, str]:
        """Load translation cache from file."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading translation cache: {e}")
        return {}
        
    def _save_cache(self) -> None:
        """Save translation cache to file."""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self._cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving translation cache: {e}")
            
    def get(self, text: str, lang: str = "ja") -> Optional[str]:
        """Get translation from cache."""
        key = f"{lang}:{text}"
        return self._cache.get(key)
        
    def set(self, text: str, translation: str, lang: str = "ja") -> None:
        """Set translation in cache."""
        key = f"{lang}:{text}"
        self._cache[key] = translation
        
        # Save periodically (every 10 translations)
        if len(self._cache) % 10 == 0:
            self._save_cache()
            
    def save(self) -> None:
        """Force save cache to file."""
        self._save_cache()
        logger.info(f"Saved {len(self._cache)} translations to cache")


class CacheManager:
    """Simple cache manager for translations."""
    
    def __init__(self, cache_name: str = "translations"):
        """Initialize cache manager."""
        cache_dir = Path("data/cache")
        cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = cache_dir / f"{cache_name}.json"
        self.cache = TranslationCache(self.cache_file)
        
    def get(self, key: str) -> Optional[str]:
        """Get value from cache."""
        return self.cache.get(key)
        
    def set(self, key: str, value: str) -> None:
        """Set value in cache."""
        self.cache.set(key, value)
        self.cache.save()  # Save immediately for translations
        
    def get_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        return {
            "total_entries": len(self.cache._cache),
            "cache_file": str(self.cache_file)
        }