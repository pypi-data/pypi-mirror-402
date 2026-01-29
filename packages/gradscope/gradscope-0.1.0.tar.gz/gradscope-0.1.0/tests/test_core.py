import pytest
import gradscope
from gradscope import attach, GradScopeRun


def test_version():
    assert gradscope.__version__ == "0.1.0"


def test_public_api_exposure():
    assert hasattr(gradscope, "attach")
    assert hasattr(gradscope, "run_summary")
    assert hasattr(gradscope, "list_runs")
    assert hasattr(gradscope, "compare_runs")
    assert hasattr(gradscope, "grad_diff")
    assert hasattr(gradscope, "export_run")
    assert hasattr(gradscope, "quick_diagnostics")


def test_attach_config(monkeypatch):
    import gradscope.monitor as mon

    class DummyBackend:
        def __init__(self, run_id, model, optimizer):
            self.run_id = run_id
            self.model = model
            self.optimizer = optimizer

    created = {}

    def fake_start_run(framework, config=None, name=None, tags=None):
        created["framework"] = framework
        created["config"] = config
        created["name"] = name
        created["tags"] = tags
        return "run-123"

    monkeypatch.setattr(mon, "TorchMonitor", DummyBackend)
    monkeypatch.setattr(mon, "RunRegistry", type("X", (), {"start_run": staticmethod(fake_start_run)}))

    model = object()
    optimizer = object()
    run = attach(model, optimizer, framework="torch", config={"lr": 0.1}, name="exp", tags={"k": "v"})

    assert isinstance(run, GradScopeRun)
    assert run.run_id == "run-123"
    assert run.name == "exp"
    assert run.tags["k"] == "v"
    assert created["framework"] == "torch"
    assert created["config"]["lr"] == 0.1
    assert created["name"] == "exp"
    assert created["tags"]["k"] == "v"


def test_infer_framework_unsupported():
    from gradscope.monitor import _infer_framework

    with pytest.raises(ValueError):
        _infer_framework(object(), object())
