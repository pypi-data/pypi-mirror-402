"""
Configuration and settings management.
"""
from typing import Dict, Any, Optional
import json
from pathlib import Path


class Config:
    """Configuration manager for engine settings."""
    
    def __init__(self):
        """Initialize configuration."""
        self._settings: Dict[str, Any] = {}
        self._defaults: Dict[str, Any] = {}
        self._load_defaults()
    
    def _load_defaults(self):
        """Load default settings."""
        self._defaults = {
            # Window
            "window.width": 1920,
            "window.height": 1080,
            "window.title": "Core",
            "window.fullscreen": False,
            "window.vsync": True,
            "window.resizable": True,
            
            # Graphics
            "graphics.api": "opengl",
            "graphics.msaa": 4,
            "graphics.anisotropic_filtering": 16,
            "graphics.shadow_resolution": 2048,
            
            # Rendering
            "rendering.max_lights": 8,
            "rendering.shadow_distance": 100.0,
            "rendering.fog_enabled": False,
            
            # Physics
            "physics.gravity": -9.81,
            "physics.timestep": 1.0 / 60.0,
            "physics.solver_iterations": 10,
            
            # Audio
            "audio.master_volume": 1.0,
            "audio.music_volume": 0.7,
            "audio.sfx_volume": 1.0,
            
            # Debug
            "debug.show_fps": True,
            "debug.show_stats": False,
            "debug.wireframe": False,
            "debug.log_level": "INFO",
        }
        
        # Initialize settings with defaults
        self._settings = self._defaults.copy()
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value.
        
        Args:
            key: Configuration key (e.g., "window.width")
            default: Default value if key not found
        
        Returns:
            Configuration value
        """
        if key in self._settings:
            return self._settings[key]
        if default is not None:
            return default
        return self._defaults.get(key)
    
    def set(self, key: str, value: Any):
        """Set configuration value."""
        self._settings[key] = value
    
    def has(self, key: str) -> bool:
        """Check if configuration key exists."""
        return key in self._settings
    
    def reset(self, key: Optional[str] = None):
        """Reset configuration to defaults."""
        if key is None:
            self._settings = self._defaults.copy()
        else:
            if key in self._defaults:
                self._settings[key] = self._defaults[key]
    
    def load_from_file(self, path: str):
        """Load configuration from JSON file."""
        file_path = Path(path)
        if file_path.exists():
            with open(file_path, 'r') as f:
                loaded = json.load(f)
                self._settings.update(loaded)
    
    def save_to_file(self, path: str):
        """Save configuration to JSON file."""
        file_path = Path(path)
        with open(file_path, 'w') as f:
            json.dump(self._settings, f, indent=2)
    
    def get_all(self) -> Dict[str, Any]:
        """Get all settings."""
        return self._settings.copy()
    
    def update(self, settings: Dict[str, Any]):
        """Update multiple settings at once."""
        self._settings.update(settings)


# Global config instance
_config_instance: Optional[Config] = None


def get_config() -> Config:
    """Get global config instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance

