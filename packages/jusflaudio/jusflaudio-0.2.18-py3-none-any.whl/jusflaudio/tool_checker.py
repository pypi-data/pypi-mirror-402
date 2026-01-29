from shutil import which
from typing import Iterable, List, Optional


def find_missing_tools(tools: Iterable[str]) -> List[str]:
    """Return a list of tools that are not available on PATH."""
    return [tool for tool in tools if which(tool) is None]


def check_whisper_dependencies() -> List[str]:
    """Check if all required dependencies for whisper functionality are available."""
    required_tools = ["ffmpeg"]  # ffmpeg is essential for audio processing
    return find_missing_tools(required_tools)


def verify_model_availability(model_name: str) -> bool:
    """
    Check if a whisper model is likely available.
    This is a basic check - actual availability is verified when loading.
    
    Args:
        model_name: Name of the whisper model (tiny.en, base.en, small, etc.)
        
    Returns:
        True if model name looks valid, False otherwise
    """
    valid_models = {
        'tiny', 'base', 'small', 'medium', 'large', 'large-v1', 'large-v2', 'large-v3',
        'tiny.en', 'base.en', 'small.en', 'medium.en', 'large.en',
        'distil-tiny.en', 'distil-base.en', 'distil-small.en', 'distil-medium.en',
        'distil-large-v2', 'distil-large-v3'
    }
    
    return model_name in valid_models


def get_available_memory_gb() -> Optional[float]:
    """
    Get available system memory in GB.
    Useful for determining if large models can be loaded.
    
    Returns:
        Available memory in GB, or None if detection failed
    """
    try:
        import psutil
        memory = psutil.virtual_memory()
        return memory.available / (1024**3)  # Convert to GB
    except ImportError:
        # psutil not available, try reading from /proc/meminfo on Linux
        try:
            with open('/proc/meminfo', 'r') as f:
                for line in f:
                    if line.startswith('MemAvailable:'):
                        kb = int(line.split()[1])
                        return kb / (1024**2)  # Convert to GB
        except (FileNotFoundError, ValueError, IndexError):
            pass
    except Exception:
        pass
        
    return None
