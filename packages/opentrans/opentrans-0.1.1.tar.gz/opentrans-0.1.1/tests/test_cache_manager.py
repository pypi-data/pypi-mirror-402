import pytest
from opentrans.cache_manager import CacheManager

@pytest.fixture
def tmp_cache(tmp_file):
    return CacheManager(tmp_file)

@pytest.fixture
def tmp_file(tmp_path):
    f = tmp_path / "test_file.txt"
    f.write_text("hello")
    return f

def test_file_exist(tmp_cache, tmp_file):
    assert (tmp_file in tmp_cache) is False

def test_cache_create_and_load(tmp_cache, tmp_file):
    tmp_cache.update(tmp_file)
    assert tmp_file in tmp_cache

def test_file_changed(tmp_cache, tmp_file):
    tmp_cache.update(tmp_file)
    tmp_file.write_text("more text")
    assert tmp_cache.file_changed(tmp_file) is True
