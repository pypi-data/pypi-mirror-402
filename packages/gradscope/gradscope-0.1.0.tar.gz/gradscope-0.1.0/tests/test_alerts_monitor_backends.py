import math

import pytest

from gradscope.alerts import AlertRules
from gradscope.storage import Storage
from gradscope.config import GradScopeConfig, set_config
from gradscope.monitor import GradScopeRun
from gradscope import utils as gs_utils


class DummyBackend:
    def __init__(self):
        self.epoch = 0
        self.step = 0
        self.closed = False
        self.rules = AlertRules()
        self.last_grad_stats = [("w", 10.0, 0.0, 10.0)]

    def set_epoch(self, epoch: int):
        self.epoch = epoch

    def close(self):
        self.closed = True


def _setup_db(tmp_path, monkeypatch):
    db_path = tmp_path / "gs_alerts.db"
    monkeypatch.setenv("GRADSCOPE_DB", str(db_path))
    set_config(GradScopeConfig(db_path=str(db_path)))
    Storage._db_path = None
    Storage._conn = None
    Storage._listeners.clear()
    Storage.init()
    return db_path


def test_alert_rules_metric_nan_inf(tmp_path, monkeypatch):
    _setup_db(tmp_path, monkeypatch)
    rules = AlertRules()
    run_id = "r1"
    Storage.insert_run(run_id, "torch", "{}", "{}")
    rules.evaluate_metric(run_id, 0, 0, "loss", math.nan, None)
    rules.evaluate_metric(run_id, 1, 0, "loss", math.inf, None)
    alerts = Storage.fetch_alerts(run_id)
    types = {a["type"] for a in alerts}
    assert "metric_nan" in types
    assert "metric_inf" in types


def test_alert_rules_metric_spike(tmp_path, monkeypatch):
    _setup_db(tmp_path, monkeypatch)
    rules = AlertRules(metric_spike_factor=2.0, window_size=5, rate_limit_steps=1, z_thresh=100.0)
    run_id = "r_metric_spike"
    Storage.insert_run(run_id, "torch", "{}", "{}")
    rules.evaluate_metric(run_id, 0, 0, "loss", 3.0, 1.0)
    alerts = Storage.fetch_alerts(run_id)
    types = {a["type"] for a in alerts}
    assert "metric_spike" in types


def test_alert_rules_metric_z_spike(tmp_path, monkeypatch):
    _setup_db(tmp_path, monkeypatch)
    rules = AlertRules(window_size=4, rate_limit_steps=1, z_thresh=1.0, metric_spike_factor=1000.0)
    run_id = "r_metric_z"
    Storage.insert_run(run_id, "torch", "{}", "{}")
    values = [1.0, 1.0, 1.0, 100.0]
    for step, v in enumerate(values):
        rules.evaluate_metric(run_id, step, 0, "loss", v, None)
    alerts = Storage.fetch_alerts(run_id)
    types = {a["type"] for a in alerts}
    assert "metric_z_spike" in types


def test_alert_rules_metric_plateau(tmp_path, monkeypatch):
    _setup_db(tmp_path, monkeypatch)
    rules = AlertRules(window_size=3, rate_limit_steps=1, metric_spike_factor=1000.0, z_thresh=1000.0)
    run_id = "r_metric_plateau"
    Storage.insert_run(run_id, "torch", "{}", "{}")
    for step in range(3):
        rules.evaluate_metric(run_id, step, 0, "loss", 1.0, None)
    alerts = Storage.fetch_alerts(run_id)
    types = {a["type"] for a in alerts}
    assert "metric_plateau" in types


def test_alert_rules_grad_vanish_and_explode(tmp_path, monkeypatch):
    _setup_db(tmp_path, monkeypatch)
    rules = AlertRules(vanish_thresh=0.5, explode_thresh=2.0, window_size=5, rate_limit_steps=1, z_thresh=100.0, cv_thresh=100.0)
    run_id = "r_grad_bounds"
    Storage.insert_run(run_id, "torch", "{}", "{}")
    rules.evaluate_gradients(run_id, 0, 0, [("w", 0.1, 0.0, 0.1)], None)
    rules.evaluate_gradients(run_id, 1, 0, [("w", 3.0, 0.0, 3.0)], None)
    alerts = Storage.fetch_alerts(run_id)
    types = {a["type"] for a in alerts}
    assert "vanish_gradient" in types
    assert "explode_gradient" in types


def test_alert_rules_weight_update_spike_and_stall(tmp_path, monkeypatch):
    _setup_db(tmp_path, monkeypatch)
    run_id = "r_updates"
    Storage.insert_run(run_id, "torch", "{}", "{}")
    rules = AlertRules(spike_factor=2.0, window_size=5, rate_limit_steps=1, z_thresh=100.0)
    rules.evaluate_weight_updates(run_id, 0, 0, [("w", 1.0)])
    rules.evaluate_weight_updates(run_id, 1, 0, [("w", 10.0)])
    rules2 = AlertRules(spike_factor=2.0, window_size=5, rate_limit_steps=1, z_thresh=100.0)
    rules2.evaluate_weight_updates(run_id, 2, 0, [("v", 1.0)])
    rules2.evaluate_weight_updates(run_id, 3, 0, [("v", 0.01)])
    alerts = Storage.fetch_alerts(run_id)
    types = {a["type"] for a in alerts}
    assert "update_spike" in types
    assert "update_stall" in types


def test_alert_rules_attribute_failure_no_gradients(tmp_path, monkeypatch):
    _setup_db(tmp_path, monkeypatch)
    rules = AlertRules()
    run_id = "r_attr_empty"
    Storage.insert_run(run_id, "torch", "{}", "{}")
    rules.attribute_failure(run_id, 0, 0, [])
    alerts = Storage.fetch_alerts(run_id)
    assert any(a["type"] == "failure_attribution" and a["message"] == "no_gradients" for a in alerts)


def test_gradscoperun_failure_marks_alert_and_attribution(tmp_path, monkeypatch):
    _setup_db(tmp_path, monkeypatch)
    run_id = "r2"
    Storage.insert_run(run_id, "torch", "{}", "{}")
    backend = DummyBackend()
    run = GradScopeRun(run_id, backend)
    run.mark_failure("boom")
    alerts = Storage.fetch_alerts(run_id)
    types = {a["type"] for a in alerts}
    assert "run_failure" in types
    assert "failure_attribution" in types
    assert any(a["type"] == "failure_attribution" and a["message"].startswith("gradient_issue:") for a in alerts)


def test_gradscoperun_context_manager_failure(tmp_path, monkeypatch):
    _setup_db(tmp_path, monkeypatch)
    run_id = "r3"
    Storage.insert_run(run_id, "torch", "{}", "{}")
    backend = DummyBackend()
    with pytest.raises(RuntimeError):
        with GradScopeRun(run_id, backend):
            raise RuntimeError("fail")
    alerts = Storage.fetch_alerts(run_id)
    assert any(a["type"] == "run_failure" for a in alerts)


def test_gradscoperun_log_metric(tmp_path, monkeypatch):
    _setup_db(tmp_path, monkeypatch)
    run_id = "r4"
    Storage.insert_run(run_id, "torch", "{}", "{}")
    backend = DummyBackend()
    run = GradScopeRun(run_id, backend)
    run.log_metric("loss", 0.5, step=0, epoch=0)
    metrics = Storage.fetch_metrics(run_id, "loss")
    assert metrics and metrics[0][2] == 0.5


def test_gradscoperun_mark_epoch_updates_backend(tmp_path, monkeypatch):
    _setup_db(tmp_path, monkeypatch)
    run_id = "r_epoch"
    Storage.insert_run(run_id, "torch", "{}", "{}")
    backend = DummyBackend()
    run = GradScopeRun(run_id, backend)
    run.mark_epoch(5)
    assert backend.epoch == 5


def test_gradscoperun_log_system_metrics(tmp_path, monkeypatch):
    _setup_db(tmp_path, monkeypatch)
    run_id = "r_sys"
    Storage.insert_run(run_id, "torch", "{}", "{}")
    backend = DummyBackend()
    run = GradScopeRun(run_id, backend)

    def fake_usage():
        return {"rss": 123456, "cpu_percent": 12.5, "gpu_mem": [1.0, 2.0], "cuda": True}

    monkeypatch.setattr(gs_utils, "system_usage", fake_usage)
    run.log_system_metrics(prefix="sys")
    metrics = Storage.fetch_metrics(run_id, "sys.rss")
    assert metrics and metrics[0][2] == 123456.0


def test_gradscoperun_alert_handler_receives_alert(tmp_path, monkeypatch):
    _setup_db(tmp_path, monkeypatch)
    run_id = "r_handler"
    Storage.insert_run(run_id, "torch", "{}", "{}")
    backend = DummyBackend()
    run = GradScopeRun(run_id, backend)
    received = []

    def handler(payload):
        received.append(payload)

    run.add_alert_handler(handler)
    Storage.insert_alert(run_id, 0, 0, "metric_nan", "loss", "critical")
    assert received and received[0]["type"] == "metric_nan"


def test_gradscoperun_summary_uses_run_summary(tmp_path, monkeypatch):
    _setup_db(tmp_path, monkeypatch)
    run_id = "r_summary"
    Storage.insert_run(run_id, "torch", "{}", "{}")
    backend = DummyBackend()
    run = GradScopeRun(run_id, backend)
    summary = run.summary()
    assert summary["run_id"] == run_id
