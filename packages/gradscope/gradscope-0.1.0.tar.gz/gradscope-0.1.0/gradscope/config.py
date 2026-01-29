from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class GradScopeConfig:
    db_path: Optional[str] = None
    flush_interval: int = 50
    vanish_thresh: float = 1e-8
    explode_thresh: float = 1e3
    spike_factor: float = 5.0
    metric_spike_factor: float = 3.0
    window_size: int = 20
    rate_limit_steps: int = 50
    z_thresh: float = 4.0
    cv_thresh: float = 2.0


_config: GradScopeConfig = None  # type: ignore[assignment]


def _env_float(name: str, default: float) -> float:
    val = os.environ.get(name)
    if val is None:
        return default
    try:
        return float(val)
    except ValueError:
        return default


def _env_int(name: str, default: int) -> int:
    val = os.environ.get(name)
    if val is None:
        return default
    try:
        return int(val)
    except ValueError:
        return default


def default_config() -> GradScopeConfig:
    return GradScopeConfig(
        db_path=os.environ.get("GRADSCOPE_DB"),
        flush_interval=_env_int("GRADSCOPE_FLUSH_INTERVAL", 50),
        vanish_thresh=_env_float("GRADSCOPE_VANISH_THRESH", 1e-8),
        explode_thresh=_env_float("GRADSCOPE_EXPLODE_THRESH", 1e3),
        spike_factor=_env_float("GRADSCOPE_SPIKE_FACTOR", 5.0),
        metric_spike_factor=_env_float("GRADSCOPE_METRIC_SPIKE_FACTOR", 3.0),
        window_size=_env_int("GRADSCOPE_WINDOW_SIZE", 20),
        rate_limit_steps=_env_int("GRADSCOPE_RATE_LIMIT_STEPS", 50),
        z_thresh=_env_float("GRADSCOPE_Z_THRESH", 4.0),
        cv_thresh=_env_float("GRADSCOPE_CV_THRESH", 2.0),
    )


def get_config() -> GradScopeConfig:
    global _config
    if _config is None:
        _config = default_config()
    return _config


def set_config(cfg: GradScopeConfig) -> None:
    global _config
    _config = cfg

