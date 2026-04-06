"""Load kompile.yaml config."""
from __future__ import annotations

import os
from pathlib import Path

import yaml


_DEFAULTS = {
    "models": {
        "filter": "claude-haiku-4-5-20251001",
        "summarize": "claude-sonnet-4-20250514",
        "compile": "claude-sonnet-4-20250514",
        "query": "claude-sonnet-4-20250514",
    },
    "paths": {
        "raw": "raw",
        "wiki": "wiki",
    },
    "context_window_limit": 0.5,
    "chunk_threshold_tokens": 80000,
}


def load_config(config_path: str | Path | None = None) -> dict:
    cfg = _deep_merge({}, _DEFAULTS)

    if config_path is None:
        config_path = Path("kompile.yaml")
    p = Path(config_path)
    if p.exists():
        user_cfg = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        cfg = _deep_merge(cfg, user_cfg)

    # API key: config file takes precedence, then env var
    if not cfg.get("api_key"):
        cfg["api_key"] = os.environ.get("ANTHROPIC_API_KEY", "")

    return cfg


def _deep_merge(base: dict, override: dict) -> dict:
    result = dict(base)
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(result.get(k), dict):
            result[k] = _deep_merge(result[k], v)
        else:
            result[k] = v
    return result
