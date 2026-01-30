import os
from pathlib import Path
from typing import Set, Tuple, Type

from pydantic import computed_field, field_validator, Field
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)

class Settings(BaseSettings):
    target_lang: str = "Chinese"
    ollama_model: str = "translategemma:4b"
    temperature: float = Field(default=1.0, ge=0.0, le=2.0)
    max_parallel_files: int = Field(default=2, gt=0)
    
    input_dir: Path = Path("./docs").resolve()
    output_dir: Path = Path("./translated").resolve()
    hash_algo: str = "sha1"
    translate_file_types: Set[str] = {".md", ".mdx", ".txt"}

    model_config = SettingsConfigDict(
        yaml_file="config.yaml",
        extra="ignore",
    )

    @computed_field
    @property
    def cache_filename(self) -> str:
        return f".{self.target_lang.lower()}_cache.json"

    @property
    def cache_path(self) -> Path:
        return self.output_dir / self.cache_filename

    @classmethod
    def check_input_directory(cls, v: Path) -> Path:
        if not v.exists():
            print(f"Warning: Input directory {v} does not exist.")
        return v

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        """Defines the priority: 1. Init, 2. Env Vars, 3. YAML File, 4. Defaults"""
        return (
            init_settings,
            env_settings,
            YamlConfigSettingsSource(settings_cls),
        )

try:
    settings = Settings()
except Exception as e:
    print(f"Configuration Error: {e}")
    raise