import hashlib
from pathlib import Path
from typing import Union


def get_file_hash(file_path: Union[str, Path], algorithm="sha256") -> str:
  """
  Generate a hash(default sha256) for a file's content.

  Args:
      file_path (str | Path): File to hash.

  Returns:
      str: hash of the file
  """
  try:
    with open(file_path, "rb") as f:
      if hasattr(hashlib, "file_digest"):
        digest = hashlib.file_digest(f, algorithm)
      else:
        digest = hashlib.new(algorithm)
        for chunk in iter(lambda: f.read(8192), b""):
            digest.update(chunk)

      return digest.hexdigest()
  except FileNotFoundError:
      raise FileNotFoundError(f"Error: File not found at {file_path}")
