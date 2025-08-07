"""Translation module for Japanese to English text."""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from functools import lru_cache

from googletrans import Translator
from loguru import logger
from tqdm import tqdm

from ..utils.cache import CacheManager
from ..utils.config import config


class DigimonTranslator:
    """Handles translation of Japanese Digimon data to English."""
    
    def __init__(self):
        """Initialize translator with caching."""
        self.translator = Translator()
        self.cache_manager = CacheManager("translations")
        self.rate_limit_delay = config.get("translation.rate_limit_delay", 1.0)
        self.batch_size = config.get("translation.batch_size", 10)
        
        # Common translations that don't need API calls
        self.static_translations = {
            # Levels
            "幼年期Ⅰ": "Baby I",
            "幼年期Ⅱ": "Baby II", 
            "幼年期": "Baby",
            "成長期": "Rookie",
            "成熟期": "Champion",
            "完全体": "Ultimate",
            "究極体": "Mega",
            "アーマー体": "Armor",
            "ハイブリッド体": "Hybrid",
            "超究極体": "Ultra",
            
            # Attributes
            "ワクチン": "Vaccine",
            "ウィルス": "Virus",
            "データ": "Data",
            "フリー": "Free",
            "バリアブル": "Variable",
            "不明": "Unknown",
            
            # Common type suffixes
            "型": " Type",
            "種": " Species",
            
            # Field labels
            "レベル": "Level",
            "タイプ": "Type",
            "属性": "Attribute",
            "必殺技": "Special Moves",
            "進化": "Evolution",
            "プロフィール": "Profile"
        }
        
    @lru_cache(maxsize=1000)
    def translate_text(self, text: str, use_cache: bool = True) -> str:
        """Translate Japanese text to English with caching."""
        if not text or not text.strip():
            return text
            
        # Check static translations first
        if text in self.static_translations:
            return self.static_translations[text]
            
        # Check cache
        if use_cache:
            cached = self.cache_manager.get(text)
            if cached:
                logger.debug(f"Cache hit for: {text[:30]}...")
                return cached
                
        try:
            # Rate limiting
            time.sleep(self.rate_limit_delay)
            
            # Translate
            result = self.translator.translate(text, src='ja', dest='en')
            translated = result.text
            
            # Cache the result
            if use_cache:
                self.cache_manager.set(text, translated)
                
            logger.debug(f"Translated: {text[:30]}... -> {translated[:30]}...")
            return translated
            
        except Exception as e:
            logger.error(f"Translation error for '{text[:50]}...': {e}")
            return text  # Return original if translation fails
            
    def translate_type(self, type_text: str) -> str:
        """Translate Digimon type with special handling."""
        if not type_text:
            return type_text
            
        # Remove common suffixes first
        base_type = type_text.replace("型", "").replace("種", "")
        
        # Try to translate the base
        translated_base = self.translate_text(base_type)
        
        # Add appropriate suffix
        if "型" in type_text:
            return f"{translated_base} Type"
        elif "種" in type_text:
            return f"{translated_base} Species"
        else:
            return translated_base
            
    def translate_digimon_data(self, digimon_data: Dict[str, Any]) -> Dict[str, Any]:
        """Translate all translatable fields in Digimon data."""
        translated = digimon_data.copy()
        
        # Translate level
        if 'info' in translated and 'level' in translated['info']:
            translated['info']['level_en'] = self.translate_text(translated['info']['level'])
            
        # Translate type
        if 'info' in translated and 'type' in translated['info']:
            translated['info']['type_en'] = self.translate_type(translated['info']['type'])
            
        # Translate attribute
        if 'info' in translated and 'attribute' in translated['info']:
            translated['info']['attribute_en'] = self.translate_text(translated['info']['attribute'])
            
        # Translate profile
        if 'profile' in translated and 'japanese' in translated['profile']:
            logger.info(f"Translating profile for {digimon_data.get('names', {}).get('english', 'Unknown')}")
            translated['profile']['english'] = self.translate_text(translated['profile']['japanese'])
            
        # Translate special moves
        if 'special_moves' in translated:
            translated['special_moves_en'] = [
                self.translate_text(move) for move in translated['special_moves']
            ]
            
        return translated
        
    def process_all_digimon(self, input_dir: Path, output_dir: Path) -> Dict[str, int]:
        """Process all Digimon JSON files and translate them."""
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Find all JSON files
        json_files = list(input_path.glob("*.json"))
        json_files = [f for f in json_files if not f.name.startswith("_")]
        
        logger.info(f"Found {len(json_files)} Digimon files to translate")
        
        stats = {
            "total": len(json_files),
            "successful": 0,
            "failed": 0,
            "skipped": 0
        }
        
        # Process in batches
        for i in tqdm(range(0, len(json_files), self.batch_size), desc="Translating batches"):
            batch = json_files[i:i + self.batch_size]
            
            for json_file in batch:
                try:
                    # Check if already translated
                    output_file = output_path / json_file.name
                    if output_file.exists():
                        with open(output_file, 'r', encoding='utf-8') as f:
                            existing = json.load(f)
                            if existing.get('translation_complete'):
                                logger.debug(f"Skipping already translated: {json_file.name}")
                                stats["skipped"] += 1
                                continue
                    
                    # Load original data
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        
                    # Translate
                    translated = self.translate_digimon_data(data)
                    translated['translation_complete'] = True
                    translated['translated_at'] = time.time()
                    
                    # Save translated data
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(translated, f, ensure_ascii=False, indent=2)
                        
                    stats["successful"] += 1
                    logger.debug(f"Translated: {json_file.name}")
                    
                except Exception as e:
                    logger.error(f"Failed to translate {json_file.name}: {e}")
                    stats["failed"] += 1
                    
            # Longer delay between batches
            if i + self.batch_size < len(json_files):
                time.sleep(self.rate_limit_delay * 3)
                
        # Save translation summary
        summary = {
            "stats": stats,
            "timestamp": time.time(),
            "cache_stats": self.cache_manager.get_stats()
        }
        
        with open(output_path / "_translation_summary.json", 'w') as f:
            json.dump(summary, f, indent=2)
            
        return stats