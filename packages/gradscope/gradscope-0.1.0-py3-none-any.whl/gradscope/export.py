import json
from typing import Dict, Iterable, Optional

from .storage import Storage


def export_run(run_id: str, include_metrics: bool = True, include_alerts: bool = True) -> Dict:
    conn = Storage._conn
    if conn is None:
        Storage.init()
        conn = Storage._conn
    cur = conn.execute("SELECT ts, framework, config, env FROM runs WHERE run_id=?", (run_id,))
    run = cur.fetchone()
    if run is None:
        raise ValueError("unknown run_id")
    cur = conn.execute("SELECT step, epoch, name, norm, mean, max FROM grad_stats WHERE run_id=?", (run_id,))
    grads = [
        {"step": s, "epoch": e, "name": n, "norm": a, "mean": b, "max": c}
        for (s, e, n, a, b, c) in cur.fetchall()
    ]
    cur = conn.execute("SELECT step, epoch, name, update_norm FROM weight_updates WHERE run_id=?", (run_id,))
    upd = [
        {"step": s, "epoch": e, "name": n, "update_norm": u}
        for (s, e, n, u) in cur.fetchall()
    ]
    alerts = []
    if include_alerts:
        cur = conn.execute("SELECT step, epoch, type, message, severity FROM alerts WHERE run_id=?", (run_id,))
        alerts = [
            {"step": s, "epoch": e, "type": t, "message": m, "severity": sev}
            for (s, e, t, m, sev) in cur.fetchall()
        ]
    cur = conn.execute("SELECT epoch, name, drift_norm FROM drift WHERE run_id=?", (run_id,))
    drift = [
        {"epoch": e, "name": n, "drift_norm": d}
        for (e, n, d) in cur.fetchall()
    ]
    metrics = []
    if include_metrics:
        cur = conn.execute("SELECT step, epoch, name, value FROM metrics WHERE run_id=?", (run_id,))
        metrics = [
            {"step": s, "epoch": e, "name": n, "value": v}
            for (s, e, n, v) in cur.fetchall()
        ]
    return {
        "run": {
            "run_id": run_id,
            "ts": run[0],
            "framework": run[1],
            "config": json.loads(run[2] or "{}"),
            "env": json.loads(run[3] or "{}"),
        },
        "grad_stats": grads,
        "weight_updates": upd,
        "alerts": alerts,
        "drift": drift,
        "metrics": metrics,
    }


def export_runs(run_ids: Iterable[str]) -> Dict:
    return {rid: export_run(rid) for rid in run_ids}


def export_run_json(run_id: str, path: Optional[str] = None, **kwargs) -> str:
    data = export_run(run_id, **kwargs)
    blob = json.dumps(data, separators=(",", ":"))
    if path is not None:
        with open(path, "w", encoding="utf-8") as f:
            f.write(blob)
    return blob
