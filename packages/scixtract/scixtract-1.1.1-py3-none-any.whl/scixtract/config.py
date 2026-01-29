"""
Configuration management for scixtract using TOML.
"""

import os
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Optional

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


@dataclass
class OllamaConfig:
    """Ollama configuration settings."""

    base_url: str = "http://localhost:11434"
    model: str = "qwen3:8b"
    timeout: int = 120
    temperature: float = 0.1
    top_p: float = 0.9
    num_ctx: int = 8192


@dataclass
class ExtractionConfig:
    """Extraction configuration settings."""

    output_dir: str = "extractions"
    update_knowledge: bool = True
    save_markdown: bool = True
    save_keywords: bool = True
    context_length: int = 200


@dataclass
class KnowledgeConfig:
    """Knowledge configuration settings."""

    db_path: Optional[str] = None
    auto_update: bool = True
    max_results: int = 20
    export_format: str = "json"


@dataclass
class Config:
    """Scixtract configuration with nested structure for CLI compatibility."""

    ollama: OllamaConfig
    extraction: ExtractionConfig
    knowledge: KnowledgeConfig

    def __init__(self) -> None:
        self.ollama = OllamaConfig()
        self.extraction = ExtractionConfig()
        self.knowledge = KnowledgeConfig()


class ConfigManager:
    """Simple TOML-based config manager."""

    CONFIG_PATHS = [
        "scixtract.toml",
        "~/.config/scixtract/config.toml",
        "~/.scixtract.toml",
    ]

    def __init__(self, config_path: Optional[str] = None):
        """Initialize config manager."""
        self.config_path = config_path
        self.config = Config()
        self.load_config()

    def find_config_file(self) -> Optional[Path]:
        """Find the first existing configuration file."""
        if self.config_path:
            config_file = Path(self.config_path).expanduser()
            if config_file.exists():
                return config_file
            else:
                raise FileNotFoundError(
                    f"Specified config file not found: {self.config_path}"
                )

        # Search for default config files
        for config_path in self.CONFIG_PATHS:
            config_file = Path(config_path).expanduser()
            if config_file.exists():
                return config_file

        return None

    def load_config(self) -> None:
        """Load configuration from TOML file and environment variables."""
        config_file = self.find_config_file()

        if config_file:
            try:
                with open(config_file, "rb") as f:
                    data = tomllib.load(f)
                self._update_from_dict(data)
            except Exception as e:
                print(f"Warning: Could not load config file {config_file}: {e}")

        # Load from environment variables (override file config)
        self._load_from_environment()

    def create_example_config(self, path: str = "scixtract.toml") -> str:
        """Create example TOML configuration file."""
        return """\
# Scixtract Configuration
# Copy to scixtract.toml and customize as needed

[ollama]
base_url = "http://localhost:11434"
model = "qwen3:8b"
timeout = 120
temperature = 0.1
top_p = 0.9
num_ctx = 8192

[extraction]
output_dir = "extractions"
update_knowledge = true
save_markdown = true
save_keywords = true
context_length = 200

[knowledge]
db_path = "knowledge.db"
auto_update = true
max_results = 20
export_format = "json"
"""

    def print_config(self) -> None:
        """Print current configuration."""
        print("📋 Scixtract Configuration:")
        print("=" * 40)

        c = self.config
        print(f"\n🤖 Ollama: {c.ollama.base_url} | {c.ollama.model}")
        print(
            f"📄 Output: {c.extraction.output_dir} | "
            f"Knowledge: {c.extraction.update_knowledge}"
        )
        print(f"🧠 Database: {c.knowledge.db_path or 'default'}")

    def _update_from_dict(self, data: dict[str, Any]) -> None:
        """Update config from dictionary data."""
        if "ollama" in data:
            ollama_data = data["ollama"]
            for key, value in ollama_data.items():
                if hasattr(self.config.ollama, key):
                    setattr(self.config.ollama, key, value)

        if "extraction" in data:
            extraction_data = data["extraction"]
            for key, value in extraction_data.items():
                if hasattr(self.config.extraction, key):
                    setattr(self.config.extraction, key, value)

        if "knowledge" in data:
            knowledge_data = data["knowledge"]
            for key, value in knowledge_data.items():
                if hasattr(self.config.knowledge, key):
                    setattr(self.config.knowledge, key, value)

    def _load_from_environment(self) -> None:
        """Load configuration from environment variables."""
        # Ollama settings
        base_url = os.getenv("SCIXTRACT_OLLAMA_BASE_URL")
        if base_url:
            self.config.ollama.base_url = base_url
        model = os.getenv("SCIXTRACT_OLLAMA_MODEL")
        if model:
            self.config.ollama.model = model
        timeout_str = os.getenv("SCIXTRACT_OLLAMA_TIMEOUT")
        if timeout_str:
            try:
                self.config.ollama.timeout = int(timeout_str)
            except ValueError:
                pass
        temperature_str = os.getenv("SCIXTRACT_OLLAMA_TEMPERATURE")
        if temperature_str:
            try:
                self.config.ollama.temperature = float(temperature_str)
            except ValueError:
                pass

        # Extraction settings
        output_dir = os.getenv("SCIXTRACT_OUTPUT_DIR")
        if output_dir:
            self.config.extraction.output_dir = output_dir
        update_knowledge = os.getenv("SCIXTRACT_UPDATE_KNOWLEDGE")
        if update_knowledge:
            self.config.extraction.update_knowledge = update_knowledge.lower() in [
                "true",
                "1",
                "yes",
            ]

        # Knowledge settings
        db_path = os.getenv("SCIXTRACT_KNOWLEDGE_DB_PATH")
        if db_path:
            self.config.knowledge.db_path = db_path

    def save_config(self, path: Optional[str] = None) -> None:
        """Save current configuration to TOML file."""
        if path:
            output_path = Path(path).expanduser()
        else:
            output_path = Path("scixtract.toml")

        # Convert config to dictionary
        config_dict = {
            "ollama": asdict(self.config.ollama),
            "extraction": asdict(self.config.extraction),
            "knowledge": asdict(self.config.knowledge),
        }

        # Create directory if needed
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            import tomli_w

            with open(output_path, "wb") as f:
                tomli_w.dump(config_dict, f)
            print(f"Configuration saved to: {output_path}")
        except ImportError:
            # Fallback to manual TOML writing
            with open(output_path, "w") as f:
                f.write("[ollama]\n")
                for key, value in config_dict["ollama"].items():
                    if isinstance(value, str):
                        f.write(f'{key} = "{value}"\n')
                    else:
                        f.write(f"{key} = {value}\n")

                f.write("\n[extraction]\n")
                for key, value in config_dict["extraction"].items():
                    if isinstance(value, str):
                        f.write(f'{key} = "{value}"\n')
                    else:
                        f.write(f"{key} = {value}\n")

                f.write("\n[knowledge]\n")
                for key, value in config_dict["knowledge"].items():
                    if value is not None:
                        if isinstance(value, str):
                            f.write(f'{key} = "{value}"\n')
                        else:
                            f.write(f"{key} = {value}\n")

            print(f"Configuration saved to: {output_path}")


def get_config(config_path: Optional[str] = None) -> Config:
    """Get configuration instance."""
    manager = ConfigManager(config_path)
    return manager.config


# Global config instance
_config_manager = None


def config() -> Config:
    """Get global config instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager.config
