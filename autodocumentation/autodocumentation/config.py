# autodocumentation/config.py
import os
import json
from typing import Dict, Any, Optional

class Config:
    """Configuration handler for AutoDocumentation."""
    
    DEFAULT_CONFIG = {
        "claude_executable": None,  # Path to Claude Desktop App
        "output_dir": "docs",       # Default output directory
        "default_format": "sphinx", # Default documentation format
        "default_language": "auto", # Default language (auto-detect)
        "model": "claude-3-opus-20240229",  # Claude model to use
        "temperature": 0.2,         # Temperature for generation
        "max_tokens": 4000,         # Maximum tokens for generation
        "prompt_templates": {
            "python": "You are an expert technical documentation writer...",
            "scala": "You are an expert Scala documentation writer...",
            "java": "You are an expert Java documentation writer..."
        }
    }
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize configuration.
        
        Args:
            config_file: Path to configuration file (default: ~/.autodocumentation.json)
        """
        self.config_file = config_file or os.path.expanduser("~/.autodocumentation.json")
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or use defaults."""
        config = self.DEFAULT_CONFIG.copy()
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                config.update(file_config)
            except Exception as e:
                print(f"Warning: Could not load config file: {e}")
        
        return config
    
    def save_config(self) -> None:
        """Save configuration to file."""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save config file: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set a configuration value."""
        self.config[key] = value
    
    def get_prompt_template(self, language: str) -> str:
        """Get the prompt template for a specific language."""
        templates = self.config.get("prompt_templates", {})
        return templates.get(language, templates.get("default", ""))