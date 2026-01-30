from .client import AllClientSettings
from collections.abc import Mapping
from pathlib import Path

__all__ = ['load_settings']

def load_settings(radkit_directory: Path | None = None, client_settings_file: Path | None = None, *, extra_settings: Mapping[str, str] | None = None) -> AllClientSettings: ...
