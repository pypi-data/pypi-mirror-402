import pytest
from pathlib import Path
from opentrans import get_file_hash

def test_file_not_found(tmp_path):
  with pytest.raises(FileNotFoundError) as excinfo:
    get_file_hash(tmp_path / "non_exist_file.txt")

def test_get_file_hash_consistency(tmp_path):
    content = b"Hello DocTrans"
    test_file = tmp_path / "hello.txt"
    test_file.write_bytes(content)

    hash_result = get_file_hash(test_file)

    expected_hash = "9806bda91dddc7547a8e57724af8348eb70a33df680c4882320599fca2238540"
    assert hash_result == expected_hash