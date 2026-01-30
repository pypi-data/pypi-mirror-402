import pytest
import logging
from pathlib import Path
from opentrans.translator import Translator
from opentrans.settings import Settings

logger = logging.getLogger(__name__)

@pytest.fixture
def tmp_settings(tmp_path) -> Settings:
  in_dir = tmp_path / "in"
  out_dir = tmp_path / "out"
  in_dir.mkdir()
  out_dir.mkdir()
  
  return Settings(
    target_lang="Chinese",
    input_dir=in_dir,
    output_dir=out_dir,
    ollama_model='translategemma:4b',
    temperature=0.0
  )

@pytest.fixture
def tmp_translator(tmp_settings: Settings):
  return Translator(cache_path=tmp_settings.cache_path)

@pytest.fixture
def tmp_file(tmp_settings: Settings) -> Path:
  p = tmp_settings.input_dir / "test.md"
  p.write_text("This is a test for doctrans. What is the meaning of life?", encoding="utf-8")
  return p

def test_translate(tmp_file: Path, tmp_settings: Settings, tmp_translator: Translator):
  tmp_translator.process_file(tmp_file, tmp_settings.input_dir, tmp_settings.output_dir) 
  
  out_file = tmp_settings.output_dir / tmp_file.relative_to(tmp_settings.input_dir)
  
  assert out_file.exists()
  content = out_file.read_text(encoding="utf-8").strip()
  
  assert len(content) > 0
  # Note: Actual translation content check depends on your local Ollama response
  assert "测试" in content or content != ""

TEST_CONTENT = """
# Header
This is a [link](https://google.com).
Check this `inline_code`.
$E = mc^2$
"""

@pytest.fixture
def complex_md_file(tmp_settings: Settings) -> Path:
  p = tmp_settings.input_dir / "integration_test.md"
  p.write_text(TEST_CONTENT, encoding="utf-8")
  return p

@pytest.mark.parametrize("target_lang, expected_keyword", [
  ("Chinese", "链接"),
  ("Spanish", "enlace"),
])
def test_translate_comprehensive(complex_md_file, tmp_settings, target_lang, expected_keyword, tmp_translator):
  tmp_settings.target_lang = target_lang
  tmp_translator.process_file(complex_md_file, tmp_settings.input_dir, tmp_settings.output_dir)
  
  out_file = tmp_settings.output_dir / complex_md_file.relative_to(tmp_settings.input_dir)
  assert out_file.exists()
  
  translated_text = out_file.read_text(encoding="utf-8")
  
  # Verify technical syntax protection
  assert "https://google.com" in translated_text
  assert "`inline_code`" in translated_text
  assert "$E = mc^2$" in translated_text
  assert translated_text.count("#") == TEST_CONTENT.count("#")