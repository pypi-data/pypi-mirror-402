"""
Configuration management for httpgo.
Supports both CLI config commands and TOML config files.
"""

import os
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Any

try:
    import tomllib  # Python 3.11+
except ImportError:
    import tomli as tomllib  # type: ignore

import tomli_w


@dataclass
class HttpgoConfig:
    """Configuration for httpgo."""
    
    # Network settings
    proxy: str | None = None
    timeout: float = 30.0
    verify_ssl: bool = True
    follow_redirects: bool = True
    
    # Default environment
    environment: str = "dev"
    
    # Output settings
    color: bool = True
    verbose: bool = False
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {k: v for k, v in asdict(self).items() if v is not None}
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "HttpgoConfig":
        """Create from dictionary."""
        # Filter only known fields
        known_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in known_fields}
        return cls(**filtered)


class ConfigManager:
    """Manages httpgo configuration from multiple sources."""
    
    # Config file locations (in priority order, later overrides earlier)
    CONFIG_PATHS = [
        Path.home() / ".config" / "httpgo" / "config.toml",  # Global config
        Path.home() / ".httpgo.toml",                         # User home
        Path("httpgo.toml"),                                  # Project local
        Path(".httpgo.toml"),                                 # Project local (hidden)
    ]
    
    def __init__(self):
        self._config: HttpgoConfig | None = None
    
    @property
    def config_dir(self) -> Path:
        """Get the global config directory."""
        config_dir = Path.home() / ".config" / "httpgo"
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir
    
    @property
    def global_config_path(self) -> Path:
        """Get the global config file path."""
        return self.config_dir / "config.toml"
    
    def load(self) -> HttpgoConfig:
        """Load configuration from all sources."""
        if self._config is not None:
            return self._config
        
        config = HttpgoConfig()
        
        # Load from config files (in order, later overrides earlier)
        for path in self.CONFIG_PATHS:
            if path.exists():
                file_config = self._load_file(path)
                config = self._merge_config(config, file_config)
        
        # Override with environment variables
        config = self._apply_env_vars(config)
        
        self._config = config
        return config
    
    def _load_file(self, path: Path) -> dict[str, Any]:
        """Load config from a TOML file."""
        try:
            with open(path, "rb") as f:
                return tomllib.load(f)
        except Exception:
            return {}
    
    def _merge_config(self, base: HttpgoConfig, overrides: dict[str, Any]) -> HttpgoConfig:
        """Merge override values into base config."""
        base_dict = base.to_dict()
        base_dict.update({k: v for k, v in overrides.items() if v is not None})
        return HttpgoConfig.from_dict(base_dict)
    
    def _apply_env_vars(self, config: HttpgoConfig) -> HttpgoConfig:
        """Apply environment variable overrides."""
        env_mapping = {
            "HTTPGO_PROXY": "proxy",
            "HTTPGO_TIMEOUT": "timeout",
            "HTTPGO_VERIFY_SSL": "verify_ssl",
            "HTTPGO_ENV": "environment",
            "HTTP_PROXY": "proxy",
            "HTTPS_PROXY": "proxy",
        }
        
        config_dict = config.to_dict()
        
        for env_var, config_key in env_mapping.items():
            value = os.environ.get(env_var)
            if value is not None:
                # Type conversion
                if config_key == "timeout":
                    config_dict[config_key] = float(value)
                elif config_key == "verify_ssl":
                    config_dict[config_key] = value.lower() in ("true", "1", "yes")
                else:
                    config_dict[config_key] = value
        
        return HttpgoConfig.from_dict(config_dict)
    
    def get(self, key: str) -> Any:
        """Get a config value."""
        config = self.load()
        return getattr(config, key, None)
    
    def set(self, key: str, value: Any, scope: str = "global") -> None:
        """Set a config value and save to file.
        
        Args:
            key: Config key to set
            value: Value to set
            scope: 'global' for ~/.config/httpgo/config.toml, 'local' for ./httpgo.toml
        """
        # Determine target file
        if scope == "local":
            config_path = Path("httpgo.toml")
        else:
            config_path = self.global_config_path
        
        # Load existing config from file
        existing = {}
        if config_path.exists():
            existing = self._load_file(config_path)
        
        # Update value
        existing[key] = value
        
        # Save
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "wb") as f:
            tomli_w.dump(existing, f)
        
        # Invalidate cache
        self._config = None
    
    def unset(self, key: str, scope: str = "global") -> bool:
        """Remove a config value.
        
        Returns:
            True if key was removed, False if key didn't exist
        """
        if scope == "local":
            config_path = Path("httpgo.toml")
        else:
            config_path = self.global_config_path
        
        if not config_path.exists():
            return False
        
        existing = self._load_file(config_path)
        if key not in existing:
            return False
        
        del existing[key]
        
        with open(config_path, "wb") as f:
            tomli_w.dump(existing, f)
        
        self._config = None
        return True
    
    def list_all(self) -> dict[str, Any]:
        """List all effective config values."""
        return self.load().to_dict()
    
    def get_config_files(self) -> list[tuple[Path, bool]]:
        """Get all config file paths and whether they exist."""
        return [(p, p.exists()) for p in self.CONFIG_PATHS]


# Global config manager instance
config_manager = ConfigManager()


def get_config() -> HttpgoConfig:
    """Get the current configuration."""
    return config_manager.load()
