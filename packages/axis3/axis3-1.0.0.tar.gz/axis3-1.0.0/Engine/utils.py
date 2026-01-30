"""
Miscellaneous utility functions for the engine.
"""
from typing import Any, Optional, List, Tuple
from pathlib import Path
import hashlib
import random
import string


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp value between min and max."""
    return max(min_val, min(max_val, value))


def lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation."""
    return a + (b - a) * t


def random_range(min_val: float, max_val: float) -> float:
    """Random float in range [min, max)."""
    return random.uniform(min_val, max_val)


def random_int(min_val: int, max_val: int) -> int:
    """Random integer in range [min, max]."""
    return random.randint(min_val, max_val)


def random_choice(sequence: List[Any]) -> Any:
    """Random choice from sequence."""
    return random.choice(sequence)


def random_string(length: int = 10, chars: str = string.ascii_letters + string.digits) -> str:
    """Generate random string."""
    return ''.join(random.choice(chars) for _ in range(length))


def hash_string(text: str) -> str:
    """Hash a string using SHA256."""
    return hashlib.sha256(text.encode()).hexdigest()


def hash_file(path: str) -> Optional[str]:
    """Hash a file using SHA256."""
    try:
        file_path = Path(path)
        if not file_path.exists():
            return None
        
        hash_obj = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()
    except Exception:
        return None


def ensure_directory(path: str) -> bool:
    """Ensure directory exists, create if not."""
    try:
        Path(path).mkdir(parents=True, exist_ok=True)
        return True
    except Exception:
        return False


def file_exists(path: str) -> bool:
    """Check if file exists."""
    return Path(path).exists()


def directory_exists(path: str) -> bool:
    """Check if directory exists."""
    return Path(path).is_dir()


def get_file_size(path: str) -> Optional[int]:
    """Get file size in bytes."""
    try:
        return Path(path).stat().st_size
    except Exception:
        return None


def get_file_extension(path: str) -> str:
    """Get file extension."""
    return Path(path).suffix.lower()


def get_file_name(path: str, with_extension: bool = True) -> str:
    """Get file name from path."""
    file_path = Path(path)
    if with_extension:
        return file_path.name
    return file_path.stem


def normalize_path(path: str) -> str:
    """Normalize path (resolve, convert separators)."""
    return str(Path(path).resolve())


def join_path(*parts: str) -> str:
    """Join path parts."""
    return str(Path(*parts))


def split_path(path: str) -> Tuple[str, str]:
    """Split path into directory and filename."""
    file_path = Path(path)
    return (str(file_path.parent), file_path.name)


def format_bytes(bytes_size: int) -> str:
    """Format bytes to human-readable string."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} PB"


def format_time(seconds: float) -> str:
    """Format seconds to human-readable string."""
    if seconds < 60:
        return f"{seconds:.2f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.2f}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours}h {minutes}m {secs:.2f}s"


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safely divide two numbers, return default if denominator is zero."""
    if abs(denominator) < 1e-9:
        return default
    return numerator / denominator


def is_numeric(value: Any) -> bool:
    """Check if value is numeric."""
    try:
        float(value)
        return True
    except (ValueError, TypeError):
        return False


def to_float(value: Any, default: float = 0.0) -> float:
    """Convert value to float, return default if conversion fails."""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def to_int(value: Any, default: int = 0) -> int:
    """Convert value to int, return default if conversion fails."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def deep_copy_dict(d: dict) -> dict:
    """Deep copy a dictionary."""
    return {k: (deep_copy_dict(v) if isinstance(v, dict) else v) for k, v in d.items()}


def merge_dicts(*dicts: dict) -> dict:
    """Merge multiple dictionaries (later dicts override earlier ones)."""
    result = {}
    for d in dicts:
        result.update(d)
    return result


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """Split list into chunks of specified size."""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def flatten_list(lst: List[Any]) -> List[Any]:
    """Flatten nested list."""
    result = []
    for item in lst:
        if isinstance(item, list):
            result.extend(flatten_list(item))
        else:
            result.append(item)
    return result


def unique_list(lst: List[Any]) -> List[Any]:
    """Get unique elements from list (preserves order)."""
    seen = set()
    result = []
    for item in lst:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result

