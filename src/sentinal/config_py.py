"""Configuration loading, validation, and profile management for SENTINAL."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Literal, Optional

try:
    import tomllib  # Python 3.11+
except ImportError:
    try:
        import tomli as tomllib  # type: ignore[no-redef]
    except ImportError:
        tomllib = None  # type: ignore[assignment]

from sentinal.errors import ConfigError

Profile = Literal["dev", "prod", "airgap", "edge_lowmem"]

_PROFILE_DEFAULTS: Dict[str, Dict[str, Any]] = {
    "dev": {
        "log_level": "DEBUG",
        "log_format": "human",
        "chunk_size": 512,
        "chunk_overlap": 64,
        "max_results": 10,
    },
    "prod": {
        "log_level": "INFO",
        "log_format": "json",
        "chunk_size": 512,
        "chunk_overlap": 64,
        "max_results": 10,
    },
    "airgap": {
        "log_level": "INFO",
        "log_format": "human",
        "chunk_size": 512,
        "chunk_overlap": 64,
        "max_results": 10,
        "offline": True,
    },
    "edge_lowmem": {
        "log_level": "WARNING",
        "log_format": "human",
        "chunk_size": 256,
        "chunk_overlap": 32,
        "max_results": 5,
    },
}

_ENV_MAP: Dict[str, str] = {
    "SENTINAL_PROFILE": "profile",
    "SENTINAL_DATA_DIR": "data_dir",
    "SENTINAL_LOG_LEVEL": "log_level",
    "SENTINAL_LOG_FORMAT": "log_format",
    "SENTINAL_CHUNK_SIZE": "chunk_size",
    "SENTINAL_CHUNK_OVERLAP": "chunk_overlap",
    "SENTINAL_MAX_RESULTS": "max_results",
}

_INT_KEYS = {"chunk_size", "chunk_overlap", "max_results"}
_VALID_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
_VALID_LOG_FORMATS = {"json", "human"}
_VALID_PROFILES = set(_PROFILE_DEFAULTS.keys())


@dataclass
class SentinalConfig:
    """Validated runtime configuration for SENTINAL."""

    profile: Profile = "dev"
    data_dir: Path = field(default_factory=lambda: Path(".sentinal"))
    log_level: str = "INFO"
    log_format: str = "human"
    chunk_size: int = 512
    chunk_overlap: int = 64
    max_results: int = 10
    offline: bool = True  # Always default offline-first

    # Derived — set after validation
    index_path: Path = field(init=False)
    db_path: Path = field(init=False)

    def __post_init__(self) -> None:
        self.data_dir = Path(self.data_dir)
        self.index_path = self.data_dir / "index"
        self.db_path = self.data_dir / "metadata.db"
        self._validate()

    def _validate(self) -> None:
        if self.profile not in _VALID_PROFILES:
            raise ConfigError(
                f"Invalid profile '{self.profile}'. "
                f"Choose from: {sorted(_VALID_PROFILES)}"
            )
        if self.log_level not in _VALID_LOG_LEVELS:
            raise ConfigError(
                f"Invalid log_level '{self.log_level}'. "
                f"Choose from: {sorted(_VALID_LOG_LEVELS)}"
            )
        if self.log_format not in _VALID_LOG_FORMATS:
            raise ConfigError(
                f"Invalid log_format '{self.log_format}'. "
                f"Choose from: {sorted(_VALID_LOG_FORMATS)}"
            )
        if self.chunk_size < 32:
            raise ConfigError(
                f"chunk_size must be >= 32, got {self.chunk_size}"
            )
        if self.chunk_overlap < 0:
            raise ConfigError(
                f"chunk_overlap must be >= 0, got {self.chunk_overlap}"
            )
        if self.chunk_overlap >= self.chunk_size:
            raise ConfigError(
                f"chunk_overlap ({self.chunk_overlap}) must be "
                f"less than chunk_size ({self.chunk_size})"
            )
        if self.max_results < 1:
            raise ConfigError(
                f"max_results must be >= 1, got {self.max_results}"
            )


def load_config(
    config_file: Optional[Path] = None,
    profile: Optional[str] = None,
) -> SentinalConfig:
    """Load and validate SENTINAL config.

    Resolution order (later wins):
      1. Profile defaults
      2. Config file values
      3. Environment variable overrides

    Args:
        config_file: Explicit path to a TOML config file.
                     Defaults to .sentinal/config.toml in the CWD.
        profile: Override profile selection.

    Returns:
        Validated SentinalConfig instance.

    Raises:
        ConfigError: On any validation or parse failure.
    """
    # 1. Determine profile early (env overrides arg)
    resolved_profile: str = profile or os.environ.get("SENTINAL_PROFILE", "dev")
    if resolved_profile not in _VALID_PROFILES:
        raise ConfigError(
            f"Invalid profile '{resolved_profile}'. "
            f"Choose from: {sorted(_VALID_PROFILES)}"
        )

    # 2. Start from profile defaults
    raw: Dict[str, Any] = dict(_PROFILE_DEFAULTS[resolved_profile])
    raw["profile"] = resolved_profile

    # 3. Load from TOML config file
    resolved_file = config_file or Path(".sentinal") / "config.toml"
    if resolved_file.exists():
        if tomllib is None:
            raise ConfigError(
                "TOML config file found but no TOML parser available. "
                "Install 'tomli' (pip install tomli) for Python < 3.11."
            )
        try:
            with open(resolved_file, "rb") as f:
                file_data = tomllib.load(f)
        except Exception as exc:
            raise ConfigError(
                f"Failed to parse config file '{resolved_file}': {exc}"
            ) from exc
        raw.update(file_data)

    # 4. Apply environment variable overrides
    for env_key, cfg_key in _ENV_MAP.items():
        val = os.environ.get(env_key)
        if val is not None:
            if cfg_key in _INT_KEYS:
                try:
                    raw[cfg_key] = int(val)
                except ValueError:
                    raise ConfigError(
                        f"Environment variable {env_key} must be an integer, "
                        f"got '{val}'"
                    )
            else:
                raw[cfg_key] = val

    try:
        return SentinalConfig(**{
            k: v for k, v in raw.items()
            if k in SentinalConfig.__dataclass_fields__
        })
    except TypeError as exc:
        raise ConfigError(f"Config construction failed: {exc}") from exc
