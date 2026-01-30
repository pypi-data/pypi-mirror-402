"""
Core - A powerful Python game engine.

This package provides a complete game engine framework including:
- Core engine with main loop
- Time and clock system
- Input system (keyboard, mouse)
- Window management
- Event system
- Resource management
- Component system (ECS)
- Configuration management
- Logging system
- Utility functions
"""

# Core
from .engine import Engine

# Time
from .time import Time, Clock, get_time

# Input
from .input import Input, Key, MouseButton, get_input

# Window
from .window import Window

# Events
from .events import Event, EventType, EventDispatcher, get_event_dispatcher

# Resources
from .resources import ResourceManager, get_resource_manager

# Components
from .components import Component, TransformComponent, Entity, EntityManager, get_entity_manager

# Config
from .config import Config, get_config

# Logger
from .logger import Logger, LogLevel, get_logger, debug, info, warning, error, critical

# Utils
from .utils import (
    clamp,
    lerp,
    random_range,
    random_int,
    random_choice,
    random_string,
    hash_string,
    hash_file,
    ensure_directory,
    file_exists,
    directory_exists,
    get_file_size,
    get_file_extension,
    get_file_name,
    normalize_path,
    join_path,
    split_path,
    format_bytes,
    format_time,
    safe_divide,
    is_numeric,
    to_float,
    to_int,
    deep_copy_dict,
    merge_dicts,
    chunk_list,
    flatten_list,
    unique_list,
)

__all__ = [
    # Core
    'Engine',
    
    # Time
    'Time',
    'Clock',
    'get_time',
    
    # Input
    'Input',
    'Key',
    'MouseButton',
    'get_input',
    
    # Window
    'Window',
    
    # Events
    'Event',
    'EventType',
    'EventDispatcher',
    'get_event_dispatcher',
    
    # Resources
    'ResourceManager',
    'get_resource_manager',
    
    # Components
    'Component',
    'TransformComponent',
    'Entity',
    'EntityManager',
    'get_entity_manager',
    
    # Config
    'Config',
    'get_config',
    
    # Logger
    'Logger',
    'LogLevel',
    'get_logger',
    'debug',
    'info',
    'warning',
    'error',
    'critical',
    
    # Utils
    'clamp',
    'lerp',
    'random_range',
    'random_int',
    'random_choice',
    'random_string',
    'hash_string',
    'hash_file',
    'ensure_directory',
    'file_exists',
    'directory_exists',
    'get_file_size',
    'get_file_extension',
    'get_file_name',
    'normalize_path',
    'join_path',
    'split_path',
    'format_bytes',
    'format_time',
    'safe_divide',
    'is_numeric',
    'to_float',
    'to_int',
    'deep_copy_dict',
    'merge_dicts',
    'chunk_list',
    'flatten_list',
    'unique_list',
]

__version__ = '1.0.0'

