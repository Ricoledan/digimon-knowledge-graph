import re
import unicodedata
from pathlib import Path
from typing import Optional, Union
import json

from loguru import logger


def sanitize_filename(name: str, max_length: int = 255) -> str:
    """
    Create safe filenames from Digimon names (handles Japanese + special chars).
    
    Args:
        name: Original filename
        max_length: Maximum filename length
        
    Returns:
        Sanitized filename safe for all platforms
    """
    # Remove/replace illegal characters for Windows/Unix
    illegal_chars = '<>:"/\\|?*'
    control_chars = ''.join(chr(i) for i in range(32))
    
    # Replace illegal characters
    for char in illegal_chars + control_chars:
        name = name.replace(char, '_')
    
    # Handle Unicode normalization
    name = unicodedata.normalize('NFKD', name)
    name = name.encode('ascii', 'ignore').decode('ascii')
    
    # Replace spaces and other problematic characters
    name = re.sub(r'[^\w\-_.]', '_', name)
    name = re.sub(r'_{2,}', '_', name)  # Remove multiple underscores
    name = name.strip('_.- ')  # Remove leading/trailing special chars
    
    # Ensure non-empty
    if not name:
        name = 'unnamed'
    
    # Truncate if too long (leave room for extension)
    if len(name) > max_length - 10:
        name = name[:max_length - 10]
    
    return name.lower()


def create_file_mapping(digimon_id: str, names: dict) -> dict:
    """
    Create consistent file mapping for a Digimon.
    
    Args:
        digimon_id: Unique identifier for the Digimon
        names: Dictionary with 'english' and 'japanese' names
        
    Returns:
        File mapping dictionary
    """
    return {
        "id": digimon_id,
        "english_name": names.get("english", ""),
        "japanese_name": names.get("japanese", ""),
        "html_file": f"data/raw/html/{digimon_id}.html",
        "image_file": f"data/raw/images/{digimon_id}.png",
        "json_file": f"data/processed/{digimon_id}.json"
    }


def save_file_mapping(mapping: dict, output_path: Union[str, Path]) -> None:
    """Save file mapping to JSON."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing mapping if it exists
    existing = {}
    if output_path.exists():
        with open(output_path, 'r', encoding='utf-8') as f:
            existing = json.load(f)
    
    # Merge with new mapping
    existing.update(mapping)
    
    # Save updated mapping
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)
        
    logger.debug(f"Updated file mapping: {output_path}")


def load_file_mapping(mapping_path: Union[str, Path]) -> dict:
    """Load file mapping from JSON."""
    mapping_path = Path(mapping_path)
    
    if not mapping_path.exists():
        logger.warning(f"File mapping not found: {mapping_path}")
        return {}
        
    with open(mapping_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def ensure_directory(path: Union[str, Path]) -> Path:
    """Ensure directory exists, create if necessary."""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_file_size_mb(file_path: Union[str, Path]) -> float:
    """Get file size in megabytes."""
    file_path = Path(file_path)
    if file_path.exists():
        return file_path.stat().st_size / (1024 * 1024)
    return 0.0


def clean_text(text: str) -> str:
    """Clean text by removing extra whitespace and normalizing."""
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove leading/trailing whitespace
    text = text.strip()
    # Normalize unicode
    text = unicodedata.normalize('NFKC', text)
    return text