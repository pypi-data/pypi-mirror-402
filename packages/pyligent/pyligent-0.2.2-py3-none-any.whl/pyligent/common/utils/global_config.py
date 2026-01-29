import os
from pathlib import Path
from typing import Any

import yaml

Config = dict[str, Any]


def load_yaml_if_exists(path: Path) -> Config:
    """Load YAML file if it exists, otherwise return empty dict."""
    if not path.is_file():
        return {}
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(f"YAML root must be a mapping: {path}")
    return data


def deep_merge(base: Config, override: Config) -> Config:
    """
    Recursively merge two dicts.

    Values from `override` take precedence over `base`.
    Nested dicts are merged; other types are replaced.
    """
    result: Config = dict(base)  # shallow copy
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_global_config(
    default_path: str | Path = "default.yaml",
    local_path: str | Path = "local.yaml",
) -> Config:
    """Load default config and optionally override with local config."""
    default_cfg = load_yaml_if_exists(Path(default_path))
    local_cfg = load_yaml_if_exists(Path(local_path))
    return deep_merge(default_cfg, local_cfg)


def export_env_from_config(config: Config, key: str = "env") -> None:
    """
    Export config[key] mapping into os.environ.

    Example: config["env"]["HF_TOKEN"] -> os.environ["HF_TOKEN"].
    """
    env_cfg = config.get(key) or {}
    if not isinstance(env_cfg, dict):
        raise ValueError(f"config['{key}'] must be a mapping if present.")
    for name, value in env_cfg.items():
        if value is None:
            continue
        os.environ[str(name)] = str(value)


def apply_global_config(
    default_path: str | Path = "default.yaml",
    local_path: str | Path = "local.yaml",
):
    global_cfg = load_global_config(default_path, local_path)
    export_env_from_config(global_cfg)
