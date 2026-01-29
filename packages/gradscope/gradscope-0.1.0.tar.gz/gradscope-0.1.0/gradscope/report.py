from typing import Dict, List

from .storage import Storage


def _ensure_conn():
    conn = Storage._conn
    if conn is None:
        Storage.init()
        conn = Storage._conn
    return conn


def run_summary(run_id: str) -> Dict:
    conn = _ensure_conn()
    cur = conn.execute(
        "SELECT max(step), max(epoch) FROM grad_stats WHERE run_id=?",
        (run_id,),
    )
    step_epoch = cur.fetchone() or (None, None)
    last_step, last_epoch = step_epoch
    cur = conn.execute(
        "SELECT type, severity, count(*) FROM alerts WHERE run_id=? GROUP BY type, severity",
        (run_id,),
    )
    alerts = cur.fetchall()
    alert_counts = {}
    for t, s, c in alerts:
        key = f"{t}:{s}"
        alert_counts[key] = c
    cur = conn.execute(
        "SELECT epoch, name, drift_norm FROM drift WHERE run_id=?",
        (run_id,),
    )
    drift_rows = cur.fetchall()
    drift_by_layer = {}
    for epoch, name, d in drift_rows:
        acc = drift_by_layer.get(name)
        if acc is None:
            drift_by_layer[name] = [d, 1]
        else:
            acc[0] += d
            acc[1] += 1
    top_drift = []
    for name, (tot, cnt) in drift_by_layer.items():
        top_drift.append((name, tot / max(cnt, 1)))
    top_drift.sort(key=lambda x: x[1], reverse=True)
    top_drift = top_drift[:10]
    cur = conn.execute(
        "SELECT name, avg(norm) AS n FROM grad_stats WHERE run_id=? GROUP BY name ORDER BY n DESC LIMIT 10",
        (run_id,),
    )
    hot_layers = cur.fetchall()
    return {
        "run_id": run_id,
        "last_step": last_step,
        "last_epoch": last_epoch,
        "alert_counts": alert_counts,
        "top_drift": top_drift,
        "hot_layers": hot_layers,
    }


def list_runs(limit: int = 50) -> List[Dict]:
    conn = _ensure_conn()
    cur = conn.execute(
        "SELECT run_id, ts, framework, config, env FROM runs ORDER BY ts DESC LIMIT ?",
        (limit,),
    )
    rows = cur.fetchall()
    out: List[Dict] = []
    import json

    for run_id, ts, framework, config, env in rows:
        cfg = json.loads(config or "{}")
        env_obj = json.loads(env or "{}")
        out.append(
            {
                "run_id": run_id,
                "ts": ts,
                "framework": framework,
                "config": cfg,
                "env": env_obj,
                "name": cfg.get("name"),
                "tags": cfg.get("tags", {}),
            }
        )
    return out


def compare_runs(run_ids: List[str]) -> Dict:
    summaries = [run_summary(rid) for rid in run_ids]
    combined_alerts: Dict[str, Dict[str, int]] = {}
    for s in summaries:
        for key, count in s["alert_counts"].items():
            d = combined_alerts.get(key)
            if d is None:
                d = {}
                combined_alerts[key] = d
            d[s["run_id"]] = count
    return {"runs": summaries, "alert_matrix": combined_alerts}


def grad_history(run_id: str, name: str) -> List[Dict]:
    conn = _ensure_conn()
    cur = conn.execute(
        "SELECT epoch, avg(norm) FROM grad_stats WHERE run_id=? AND name=? GROUP BY epoch ORDER BY epoch ASC",
        (run_id, name),
    )
    rows = cur.fetchall()
    return [{"epoch": e, "norm": n} for e, n in rows]


def metric_history(run_id: str, name: str) -> List[Dict]:
    conn = _ensure_conn()
    cur = conn.execute(
        "SELECT step, epoch, value FROM metrics WHERE run_id=? AND name=? ORDER BY step ASC",
        (run_id, name),
    )
    rows = cur.fetchall()
    return [
        {"step": step, "epoch": epoch, "value": value}
        for step, epoch, value in rows
    ]


def quick_diagnostics(run_id: str) -> Dict:
    s = run_summary(run_id)
    alerts = s["alert_counts"]
    bad_types = [
        "explode_gradient:critical",
        "run_failure:critical",
        "metric_nan:critical",
        "metric_inf:critical",
    ]
    issues = []
    for key in bad_types:
        c = alerts.get(key, 0)
        if c:
            issues.append({"type": key, "count": c})

    ok = not issues

    recommendations = []
    if alerts.get("explode_gradient:critical", 0):
        recommendations.append("Gradients exploded; consider lowering learning rate or using gradient clipping.")
    if alerts.get("metric_nan:critical", 0) or alerts.get("metric_inf:critical", 0):
        recommendations.append("Metrics contain NaN/Inf; check loss function, data preprocessing, and numerical stability.")
    if alerts.get("run_failure:critical", 0):
        recommendations.append("Run failed; inspect the last few alerts and training logs for root cause.")
    if alerts.get("vanish_gradient:high", 0):
        recommendations.append("Gradients vanishing; consider increasing learning rate or revisiting network depth/activation.")
    if alerts.get("metric_plateau:info", 0):
        recommendations.append("Primary metric plateaued; consider learning rate schedule, regularization, or model capacity.")

    return {
        "run_id": run_id,
        "ok": ok,
        "issues": issues,
        "summary": s,
        "recommendations": recommendations,
    }


