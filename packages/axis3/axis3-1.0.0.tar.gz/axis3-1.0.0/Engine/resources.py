"""
Resource management system for loading and caching assets.
"""
from typing import Dict, TypeVar, Generic, Optional, Callable, Any
from pathlib import Path
import json


T = TypeVar('T')


class ResourceManager:
    """Manages loading and caching of resources."""
    
    def __init__(self):
        """Initialize resource manager."""
        self._resources: Dict[str, Any] = {}
        self._loaders: Dict[str, Callable[[str], Any]] = {}
        self._resource_paths: Dict[str, Path] = {}
        self._base_path = Path(".")
    
    def set_base_path(self, path: str):
        """Set base path for resources."""
        self._base_path = Path(path)
    
    def get_base_path(self) -> Path:
        """Get base path."""
        return self._base_path
    
    def register_loader(self, extension: str, loader: Callable[[str], Any]):
        """
        Register a loader function for a file extension.
        
        Args:
            extension: File extension (e.g., '.png', '.json')
            loader: Loader function that takes a path and returns the resource
        """
        self._loaders[extension.lower()] = loader
    
    def load(self, path: str, force_reload: bool = False) -> Any:
        """
        Load a resource.
        
        Args:
            path: Resource path (relative to base path)
            force_reload: Force reload even if already cached
        
        Returns:
            Loaded resource
        """
        # Normalize path
        full_path = self._base_path / path
        path_str = str(full_path.resolve())
        
        # Check cache
        if not force_reload and path_str in self._resources:
            return self._resources[path_str]
        
        # Determine loader
        extension = full_path.suffix.lower()
        if extension not in self._loaders:
            raise ValueError(f"No loader registered for extension: {extension}")
        
        # Load resource
        loader = self._loaders[extension]
        resource = loader(str(full_path))
        
        # Cache
        self._resources[path_str] = resource
        self._resource_paths[path_str] = full_path
        
        return resource
    
    def get(self, path: str) -> Optional[Any]:
        """Get cached resource without loading."""
        full_path = self._base_path / path
        path_str = str(full_path.resolve())
        return self._resources.get(path_str)
    
    def unload(self, path: str):
        """Unload a resource from cache."""
        full_path = self._base_path / path
        path_str = str(full_path.resolve())
        if path_str in self._resources:
            del self._resources[path_str]
        if path_str in self._resource_paths:
            del self._resource_paths[path_str]
    
    def clear(self):
        """Clear all cached resources."""
        self._resources.clear()
        self._resource_paths.clear()
    
    def is_loaded(self, path: str) -> bool:
        """Check if resource is loaded."""
        full_path = self._base_path / path
        path_str = str(full_path.resolve())
        return path_str in self._resources
    
    def get_resource_count(self) -> int:
        """Get number of loaded resources."""
        return len(self._resources)


# Built-in loaders
def load_text_file(path: str) -> str:
    """Load text file."""
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def load_json_file(path: str) -> dict:
    """Load JSON file."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_binary_file(path: str) -> bytes:
    """Load binary file."""
    with open(path, 'rb') as f:
        return f.read()


# Global resource manager instance
_resource_manager: Optional[ResourceManager] = None


def get_resource_manager() -> ResourceManager:
    """Get global resource manager instance."""
    global _resource_manager
    if _resource_manager is None:
        _resource_manager = ResourceManager()
        # Register default loaders
        _resource_manager.register_loader('.txt', load_text_file)
        _resource_manager.register_loader('.json', load_json_file)
        _resource_manager.register_loader('.bin', load_binary_file)
    return _resource_manager

