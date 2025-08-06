import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from dotenv import load_dotenv
from loguru import logger


class Config:
    """Configuration management for the Digimon Knowledge Graph project."""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize configuration from YAML file and environment variables."""
        self.config_path = Path(config_path)
        self._config: Dict[str, Any] = {}
        
        # Load environment variables
        load_dotenv()
        
        # Load configuration
        self._load_config()
        self._substitute_env_vars()
        self._validate_config()
        
    def _load_config(self) -> None:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
            
        with open(self.config_path, 'r') as f:
            self._config = yaml.safe_load(f)
            
        logger.info(f"Loaded configuration from {self.config_path}")
        
    def _substitute_env_vars(self) -> None:
        """Substitute environment variables in configuration values."""
        def substitute(value: Any) -> Any:
            if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                env_var = value[2:-1]
                return os.getenv(env_var, value)
            elif isinstance(value, dict):
                return {k: substitute(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [substitute(v) for v in value]
            return value
            
        self._config = substitute(self._config)
        
    def _validate_config(self) -> None:
        """Validate required configuration values."""
        required_keys = [
            "scraping.base_url",
            "neo4j.uri",
            "paths.data_dir"
        ]
        
        for key in required_keys:
            if self.get(key) is None:
                raise ValueError(f"Required configuration key missing: {key}")
                
        # Create directories if they don't exist
        for path_key in ["data_dir", "raw_html", "raw_images", "processed_data", "cache_dir", "logs_dir"]:
            path = self.get(f"paths.{path_key}")
            if path:
                Path(path).mkdir(parents=True, exist_ok=True)
                
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation."""
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
                
        return value
        
    def set(self, key: str, value: Any) -> None:
        """Set configuration value using dot notation."""
        keys = key.split('.')
        config = self._config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
            
        config[keys[-1]] = value
        
    @property
    def scraping(self) -> Dict[str, Any]:
        """Get scraping configuration."""
        return self._config.get("scraping", {})
        
    @property
    def neo4j(self) -> Dict[str, Any]:
        """Get Neo4j configuration."""
        return self._config.get("neo4j", {})
        
    @property
    def paths(self) -> Dict[str, Any]:
        """Get paths configuration."""
        return self._config.get("paths", {})
        
    @property
    def logging_config(self) -> Dict[str, Any]:
        """Get logging configuration."""
        return self._config.get("logging", {})
        
    def __repr__(self) -> str:
        return f"Config(config_path='{self.config_path}')"


# Global configuration instance
config = Config()