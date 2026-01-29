import json

from gradscope.storage import Storage
from gradscope.diff import grad_diff, grad_diff_summary, grad_diff_cross_run, grad_diff_filtered, grad_diff_ranked
from gradscope.export import export_run, export_run_json, export_runs


def _basic_run(run_id: str):
    Storage.insert_grad_stats_batch([
        (run_id, 0, 0, "w1", 1.0, 0.0, 1.0),
        (run_id, 0, 0, "w2", 2.0, 0.0, 2.0),
    ])


def test_diff_and_export(tmp_path, monkeypatch):
    from gradscope.config import GradScopeConfig, set_config

    db_path = tmp_path / "gs.db"
    monkeypatch.setenv("GRADSCOPE_DB", str(db_path))
    set_config(GradScopeConfig(db_path=str(db_path)))
    Storage._db_path = None
    Storage._conn = None
    Storage._listeners.clear()
    Storage.init()

    Storage.insert_run("a", "torch", "{}", "{}")
    Storage.insert_run("b", "torch", "{}", "{}")
    _basic_run("a")
    _basic_run("b")
    Storage.insert_grad_stats_batch([("a", 0, 1, "w1", 3.0, 0.0, 3.0)])
    Storage.insert_grad_stats_batch([("b", 0, 1, "w1", 4.0, 0.0, 4.0)])

    d = grad_diff("a", 0, 1)
    assert "w1" in d and d["w1"] == 2.0

    summary = grad_diff_summary("a", 0, 1, top_k=1)
    assert summary["increases"][0][0] == "w1"
    assert summary["decreases"]
    assert summary["l2_delta"] > 0.0

    cross = grad_diff_cross_run("a", "b", epoch_a=1, epoch_b=1)
    assert cross["w1"] == 1.0

    filt = grad_diff_filtered("a", 0, 1, min_norm=1.5, name_contains="w1")
    assert set(filt.keys()) == {"w1"}

    ranked_abs = grad_diff_ranked("a", 0, 1, top_k=2, by_abs=True)
    ranked_signed = grad_diff_ranked("a", 0, 1, top_k=2, by_abs=False)
    assert len(ranked_abs) == 2
    assert len(ranked_signed) == 2

    data = export_run("a")
    assert data["run"]["run_id"] == "a"
    assert data["alerts"] == []

    blob = export_run_json("a")
    parsed = json.loads(blob)
    assert parsed["run"]["run_id"] == "a"

    no_ma = export_run("a", include_metrics=False, include_alerts=False)
    assert no_ma["metrics"] == []
    assert no_ma["alerts"] == []

    out_path = tmp_path / "run_a.json"
    blob2 = export_run_json("a", path=str(out_path), include_metrics=False, include_alerts=False)
    assert out_path.is_file()
    with out_path.open("r", encoding="utf-8") as f:
        on_disk = json.loads(f.read())
    assert on_disk["run"]["run_id"] == "a"
    assert blob2 == json.dumps(on_disk, separators=(",", ":"))

    multi = export_runs(["a", "b"])
    assert set(multi.keys()) == {"a", "b"}
