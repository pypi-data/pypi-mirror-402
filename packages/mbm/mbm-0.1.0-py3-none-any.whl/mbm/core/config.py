"""
MBM Configuration

Handles all configuration management including user preferences,
paths, and runtime settings.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from platformdirs import user_cache_dir, user_config_dir, user_data_dir

from mbm.core.constants import APP_NAME, APP_VERSION


@dataclass
class MBMConfig:
    """
    Central configuration class for MBM CLI.
    
    Manages paths, user preferences, and runtime settings with
    cross-platform support.
    """
    
    # Application metadata
    app_name: str = APP_NAME
    app_version: str = APP_VERSION
    
    # Paths (lazily initialized)
    _config_dir: Optional[Path] = field(default=None, repr=False)
    _cache_dir: Optional[Path] = field(default=None, repr=False)
    _data_dir: Optional[Path] = field(default=None, repr=False)
    _temp_dir: Optional[Path] = field(default=None, repr=False)
    
    # User preferences
    color_enabled: bool = True
    verbose: bool = False
    debug: bool = False
    
    # NLP settings
    nlp_enabled: bool = True
    spacy_model: str = "en_core_web_sm"
    
    # Media settings
    auto_cleanup_media: bool = True
    media_timeout: int = 10
    
    @property
    def config_dir(self) -> Path:
        """Get or create the configuration directory."""
        if self._config_dir is None:
            self._config_dir = Path(user_config_dir(self.app_name, ensure_exists=True))
        return self._config_dir
    
    @property
    def cache_dir(self) -> Path:
        """Get or create the cache directory."""
        if self._cache_dir is None:
            self._cache_dir = Path(user_cache_dir(self.app_name, ensure_exists=True))
        return self._cache_dir
    
    @property
    def data_dir(self) -> Path:
        """Get or create the data directory."""
        if self._data_dir is None:
            self._data_dir = Path(user_data_dir(self.app_name, ensure_exists=True))
        return self._data_dir
    
    @property
    def temp_dir(self) -> Path:
        """Get or create the temporary media directory."""
        if self._temp_dir is None:
            import tempfile
            self._temp_dir = Path(tempfile.gettempdir()) / self.app_name.lower() / "media"
            self._temp_dir.mkdir(parents=True, exist_ok=True)
        return self._temp_dir
    
    @property
    def config_file(self) -> Path:
        """Path to the main configuration file."""
        return self.config_dir / "config.json"
    
    def load(self) -> MBMConfig:
        """Load configuration from file."""
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._apply_config(data)
            except (json.JSONDecodeError, IOError) as e:
                # Use defaults if config file is corrupted
                if self.verbose:
                    print(f"Warning: Could not load config: {e}")
        return self
    
    def save(self) -> None:
        """Save current configuration to file."""
        data = {
            "color_enabled": self.color_enabled,
            "verbose": self.verbose,
            "debug": self.debug,
            "nlp_enabled": self.nlp_enabled,
            "spacy_model": self.spacy_model,
            "auto_cleanup_media": self.auto_cleanup_media,
            "media_timeout": self.media_timeout,
        }
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except IOError as e:
            if self.verbose:
                print(f"Warning: Could not save config: {e}")
    
    def _apply_config(self, data: dict[str, Any]) -> None:
        """Apply configuration dictionary to this instance."""
        if "color_enabled" in data:
            self.color_enabled = bool(data["color_enabled"])
        if "verbose" in data:
            self.verbose = bool(data["verbose"])
        if "debug" in data:
            self.debug = bool(data["debug"])
        if "nlp_enabled" in data:
            self.nlp_enabled = bool(data["nlp_enabled"])
        if "spacy_model" in data:
            self.spacy_model = str(data["spacy_model"])
        if "auto_cleanup_media" in data:
            self.auto_cleanup_media = bool(data["auto_cleanup_media"])
        if "media_timeout" in data:
            self.media_timeout = int(data["media_timeout"])
    
    def cleanup_temp_files(self) -> int:
        """
        Clean up temporary media files.
        
        Returns:
            Number of files deleted.
        """
        count = 0
        if self.temp_dir.exists():
            for file in self.temp_dir.iterdir():
                if file.is_file():
                    try:
                        file.unlink()
                        count += 1
                    except OSError:
                        pass
        return count
    
    @classmethod
    def get_default(cls) -> MBMConfig:
        """Get a default configuration instance."""
        return cls().load()


# Global configuration instance
_config: Optional[MBMConfig] = None


def get_config() -> MBMConfig:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = MBMConfig.get_default()
    return _config


def set_config(config: MBMConfig) -> None:
    """Set the global configuration instance."""
    global _config
    _config = config
