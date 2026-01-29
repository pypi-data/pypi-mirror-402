import json
import subprocess
import sys

import pytest

from fastapi.testclient import TestClient

from gradscope.server import create_app
from gradscope.storage import Storage
from gradscope.config import GradScopeConfig, set_config


def _setup_db(tmp_path, monkeypatch):
    db_path = tmp_path / "gs_api.db"
    monkeypatch.setenv("GRADSCOPE_DB", str(db_path))
    set_config(GradScopeConfig(db_path=str(db_path)))
    Storage._db_path = None
    Storage._conn = None
    Storage._listeners.clear()
    Storage.init()
    return db_path


def _seed_run():
    env = {"git": "deadbeef", "git_branch": "main", "git_dirty": False}
    Storage.insert_run("run1", "torch", "{}", json.dumps(env))
    Storage.insert_grad_stats_batch([
        ("run1", 0, 0, "w", 1.0, 0.0, 1.0),
    ])
    Storage.insert_metric("run1", 0, 0, "loss", 0.5)
    Storage.insert_alert("run1", 0, 0, "explode_gradient", "w", "critical")


def _seed_runs_for_cli():
    env_a = {"git": "aaaa1111", "git_branch": "exp", "git_dirty": True}
    env_b = {"git": "bbbb2222", "git_branch": "main", "git_dirty": False}
    Storage.insert_run("a", "torch", "{}", json.dumps(env_a))
    Storage.insert_run("b", "torch", "{}", json.dumps(env_b))
    Storage.insert_grad_stats_batch([
        ("a", 0, 0, "w1", 1.0, 0.0, 1.0),
        ("a", 0, 1, "w1", 3.0, 0.0, 3.0),
        ("b", 0, 0, "w1", 2.0, 0.0, 2.0),
        ("b", 0, 1, "w1", 4.0, 0.0, 4.0),
    ])
    Storage.insert_metric("a", 0, 0, "loss", 0.5)
    Storage.insert_alert("a", 0, 0, "explode_gradient", "w1", "critical")


def test_api_runs_and_compare(tmp_path, monkeypatch):
    _setup_db(tmp_path, monkeypatch)
    _seed_run()
    app = create_app()
    client = TestClient(app)

    r = client.get("/runs")
    assert r.status_code == 200
    data = r.json()
    assert any(d["run_id"] == "run1" for d in data)

    r = client.get("/runs", params={"git": "deadbeef"})
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1 and data[0]["run_id"] == "run1"

    r = client.get("/runs", params={"git_branch": "main"})
    assert r.status_code == 200
    data = r.json()
    assert any(d["run_id"] == "run1" for d in data)

    r = client.get("/runs/run1")
    assert r.status_code == 200
    run = r.json()
    assert run["run_id"] == "run1"

    r = client.get("/runs/run1/summary")
    assert r.status_code == 200
    summary = r.json()
    assert summary["run_id"] == "run1"

    r = client.get("/runs/run1/alerts")
    assert r.status_code == 200
    alerts = r.json()
    assert alerts and alerts[0]["type"] == "explode_gradient"

    r = client.get("/compare", params=[("run_id", "run1")])
    assert r.status_code == 200
    body = r.json()
    assert "runs" in body

    r = client.get("/runs/run1/metrics/loss")
    assert r.status_code == 200
    metrics = r.json()
    assert metrics and metrics[0]["value"] == 0.5

    r = client.get("/runs/run1/grads/w")
    assert r.status_code == 200
    grads = r.json()
    assert grads and grads[0]["epoch"] == 0

    r = client.get("/runs/run1/diagnostics")
    assert r.status_code == 200
    diag = r.json()
    assert diag["run_id"] == "run1"
    assert isinstance(diag.get("recommendations"), list)


def test_api_get_run_not_found(tmp_path, monkeypatch):
    _setup_db(tmp_path, monkeypatch)
    _seed_run()
    app = create_app()
    client = TestClient(app)
    r = client.get("/runs/unknown")
    assert r.status_code == 404
    body = r.json()
    assert body.get("detail") == "run not found"


def test_cli_version():
    out = subprocess.check_output([sys.executable, "-m", "gradscope.cli", "version"], text=True)
    assert "gradscope" in out


def test_cli_commands_main(tmp_path, monkeypatch, capsys):
    _setup_db(tmp_path, monkeypatch)
    _seed_runs_for_cli()
    import gradscope.cli as cli

    cli.main(["list", "--limit", "10"])
    out = capsys.readouterr().out
    assert "a" in out and "b" in out

    cli.main(["list", "--limit", "10", "--git", "aaaa1111"])
    out = capsys.readouterr().out
    assert "a" in out and "b" not in out

    cli.main(["list", "--limit", "10", "--git-branch", "main"])
    out = capsys.readouterr().out
    assert "b" in out and "a" not in out

    cli.main(["list", "--limit", "10", "--dirty"])
    out = capsys.readouterr().out
    assert "a" in out and "b" not in out

    cli.main(["list", "--limit", "10", "--clean"])
    out = capsys.readouterr().out
    assert "b" in out and "a" not in out

    cli.main(["summary", "a"])
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["run_id"] == "a"

    cli.main(["compare", "a", "b"])
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "runs" in data and len(data["runs"]) == 2

    cli.main(["diff", "epoch", "a", "0", "1", "--top-k", "5"])
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "summary" in data and "ranked" in data

    cli.main(["diff", "cross", "a", "b", "--epoch-a", "1", "--epoch-b", "1", "--top-k", "5"])
    out = capsys.readouterr().out
    data = json.loads(out)
    assert isinstance(data, list) and data

    cli.main(["export", "a"])
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["run"]["run_id"] == "a"

    cli.main(["diagnose", "a"])
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["run_id"] == "a" and "issues" in data
