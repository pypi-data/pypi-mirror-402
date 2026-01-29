import json
import os

import pytest

from gradscope.config import default_config, get_config, set_config, GradScopeConfig
from gradscope.storage import Storage
from gradscope.registry import RunRegistry
from gradscope.report import run_summary, list_runs, grad_history, metric_history, quick_diagnostics


def _use_temp_db(tmp_path, monkeypatch):
    db_path = tmp_path / "gs.db"
    monkeypatch.setenv("GRADSCOPE_DB", str(db_path))
    set_config(GradScopeConfig(db_path=str(db_path)))
    Storage._db_path = None
    Storage._conn = None
    Storage._listeners.clear()
    Storage.init()
    return db_path


def test_default_config_env_override(monkeypatch):
    monkeypatch.setenv("GRADSCOPE_FLUSH_INTERVAL", "123")
    cfg = default_config()
    assert cfg.flush_interval == 123


def test_default_config_invalid_env(monkeypatch):
    monkeypatch.setenv("GRADSCOPE_WINDOW_SIZE", "not-an-int")
    cfg = default_config()
    assert cfg.window_size == 20


def test_get_config_and_set_config_roundtrip():
    cfg = GradScopeConfig(
        db_path="/tmp/gs.db",
        flush_interval=7,
        vanish_thresh=1e-9,
        explode_thresh=1e2,
        spike_factor=2.0,
        metric_spike_factor=4.0,
        window_size=10,
        rate_limit_steps=5,
        z_thresh=2.5,
        cv_thresh=1.5,
    )
    set_config(cfg)
    got = get_config()
    assert got is cfg


def test_storage_and_registry_and_report_flow(tmp_path, monkeypatch):
    _use_temp_db(tmp_path, monkeypatch)

    run_id = RunRegistry.start_run("torch", {"lr": 0.1}, name="test", tags={"a": "b"})

    Storage.insert_grad_stats_batch([(run_id, 0, 0, "w", 1.0, 0.1, 0.5)])
    Storage.insert_metric(run_id, 0, 0, "loss", 0.5)
    Storage.insert_drift_batch([(run_id, 0, "w", 0.2)])
    Storage.insert_alert(run_id, 0, 0, "explode_gradient", "w", "critical")

    s = run_summary(run_id)
    assert s["run_id"] == run_id
    assert s["last_step"] == 0
    assert s["last_epoch"] == 0
    assert s["alert_counts"]["explode_gradient:critical"] == 1
    assert s["top_drift"]
    assert s["hot_layers"]

    runs = list_runs(limit=10)
    assert any(r["run_id"] == run_id for r in runs)
    entry = next(r for r in runs if r["run_id"] == run_id)
    assert entry["name"] == "test"
    assert entry["tags"]["a"] == "b"

    gh = grad_history(run_id, "w")
    assert gh and gh[0]["epoch"] == 0

    mh = metric_history(run_id, "loss")
    assert mh and mh[0]["value"] == 0.5

    diag = quick_diagnostics(run_id)
    assert diag["run_id"] == run_id
    assert diag["ok"] is False
    assert any(i["type"] == "explode_gradient:critical" for i in diag["issues"])


def test_runregistry_start_run_and_get_config(tmp_path, monkeypatch):
    _use_temp_db(tmp_path, monkeypatch)
    run_id = RunRegistry.start_run("torch", {"lr": 0.01}, name="exp1", tags={"k": "v"})
    cfg = RunRegistry.get_run_config(run_id)
    assert cfg is not None
    assert cfg["lr"] == 0.01
    assert cfg["name"] == "exp1"
    assert cfg["tags"]["k"] == "v"


def test_runregistry_get_run_config_unknown(tmp_path, monkeypatch):
    _use_temp_db(tmp_path, monkeypatch)
    cfg = RunRegistry.get_run_config("missing")
    assert cfg is None


def test_registry_update_tags(tmp_path, monkeypatch):
    _use_temp_db(tmp_path, monkeypatch)
    run_id = RunRegistry.start_run("torch")
    RunRegistry.update_tags(run_id, {"x": "1"})
    cfg = RunRegistry.get_run_config(run_id)
    assert cfg is not None
    assert cfg["tags"]["x"] == "1"


def test_quick_diagnostics_recommendations(tmp_path, monkeypatch):
    _use_temp_db(tmp_path, monkeypatch)
    run_id = "rdiag"
    Storage.insert_alert(run_id, 0, 0, "explode_gradient", "w", "critical")
    Storage.insert_alert(run_id, 0, 0, "metric_nan", "loss", "critical")
    Storage.insert_alert(run_id, 0, 0, "metric_inf", "loss", "critical")
    Storage.insert_alert(run_id, 0, 0, "run_failure", "err", "critical")
    Storage.insert_alert(run_id, 0, 0, "vanish_gradient", "w", "high")
    Storage.insert_alert(run_id, 0, 0, "metric_plateau", "loss", "info")
    diag = quick_diagnostics(run_id)
    assert diag["ok"] is False
    recs = "\n".join(diag["recommendations"])
    assert "Gradients exploded" in recs
    assert "Metrics contain NaN/Inf" in recs
    assert "Run failed" in recs
    assert "Gradients vanishing" in recs
    assert "Primary metric plateaued" in recs
