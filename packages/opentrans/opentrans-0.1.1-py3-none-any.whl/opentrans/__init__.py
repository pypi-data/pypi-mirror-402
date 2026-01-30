__version__ = "v0.1.1"

from .cache_manager import CacheManager
from .hasher import get_file_hash

__all__ = ['get_file_hash']