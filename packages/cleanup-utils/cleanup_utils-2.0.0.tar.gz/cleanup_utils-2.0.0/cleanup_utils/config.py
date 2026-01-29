#!/usr/bin/env python3

from functools import cache
from pathlib import Path
from . import __app_name__

from yaml import safe_load

# cache_dir_exemptions_relative_path = [
#     'tealdeer', 'JetBrains', 'ms-playwright', 'typescript', 'lima',
#     'com.nssurge.surge-mac', 'pypoetry'
# ]

library_cache_path = Path.home() / "Library/Caches"
pypoetry_path = library_cache_path / "pypoetry" / "cache"
pypoetry_cache_path = library_cache_path / "pypoetry" / "cache"
vscode_app_dir = Path.home() / "Library/Application Support/Code"
vscode_insiders_app_dir = Path.home() / "Library/Application Support/Code - Insiders"
vscode_user_workspaceStorage_dir = vscode_app_dir / "User/workspaceStorage"
vscode_insiders_user_workspaceStorage_dir = (
    vscode_insiders_app_dir / "User/workspaceStorage"
)


CONFIG_DIR = Path.home() / ".config" / __app_name__
CONFIG_FILE = CONFIG_DIR / "config.yaml"


@cache
def read_config():
    if not CONFIG_FILE.exists():
        return {}
    with CONFIG_FILE.open() as f:
        data = safe_load(f)
        return data or {}
