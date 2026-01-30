import json
import os
from pathlib import Path
from .hasher import get_file_hash
from typing import Union
from .settings import settings

class CacheManager:
  """
  Change Cache
  """
  def __init__(self, cache_file: Path):
    self.cache_file = cache_file
    self.cache = self._load_cache()
  
  def __del__(self):
    self.save() 

  def _load_cache(self) -> dict:
    """
    Docstring for _load_cache
    
    :return: file_path and hash in dict format from cache file
    :rtype: dict
    """ 
    if self.cache_file == None:
      return {}

    if not self.cache_file.exists():
      self.cache_file.parent.mkdir(parents=True, exist_ok=True)
      with open(self.cache_file, 'w') as f:
        json.dump({}, f, indent=2)
    
    try:
      with open(self.cache_file, "r") as f:
        return json.load(f)
    except (json.JSONDecodeError, IOError):
      return {}
    return {}
  
  def file_changed(self, file_path: Union[Path, str]) -> bool:
    """
    Check if the hash changed

    Args:
        file_path (Path): file to check

    Returns:
        bool: True if changed else False
    """
    return self.cache.get(str(file_path)) != get_file_hash(file_path, settings.hash_algo)
  
  def __contains__(self, file_path: Union[Path, str]):
    return str(file_path) in self.cache
   
  def update(self, file_path: Path):
    """
    Update the file hash in cache. Create the file if not exist.

    Args:
        file_path (Path): File to update
    """
    self.cache[str(file_path)] = get_file_hash(file_path, settings.hash_algo)
  
  def save(self):
    with open(self.cache_file, "w") as f:
      json.dump(self.cache, f, indent=2)
        
