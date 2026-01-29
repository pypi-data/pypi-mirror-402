import os
import sqlite3
import threading
from typing import List, Tuple, Optional, Callable, Dict, Any
from .utils import ensure_dir
from .config import get_config


class Storage:
    _db_path = None
    _conn = None
    _lock = threading.Lock()
    _listeners: List[Callable[[str, Dict], None]] = []

    @classmethod
    def init(cls):
        if cls._db_path is None:
            cfg = get_config()
            cls._db_path = cfg.db_path or os.environ.get("GRADSCOPE_DB") or os.path.join(os.getcwd(), ".gradscope", "gradscope.db")
        ensure_dir(os.path.dirname(cls._db_path))
        cls._conn = sqlite3.connect(cls._db_path, check_same_thread=False)
        cls._conn.execute("PRAGMA journal_mode=WAL;")
        cls._conn.execute(
            "CREATE TABLE IF NOT EXISTS runs (run_id TEXT PRIMARY KEY, ts INTEGER, framework TEXT, config TEXT, env TEXT)"
        )
        cls._conn.execute(
            "CREATE TABLE IF NOT EXISTS grad_stats (run_id TEXT, step INTEGER, epoch INTEGER, name TEXT, norm REAL, mean REAL, max REAL)"
        )
        cls._conn.execute(
            "CREATE TABLE IF NOT EXISTS weight_updates (run_id TEXT, step INTEGER, epoch INTEGER, name TEXT, update_norm REAL)"
        )
        cls._conn.execute(
            "CREATE TABLE IF NOT EXISTS alerts (run_id TEXT, step INTEGER, epoch INTEGER, type TEXT, message TEXT, severity TEXT)"
        )
        cls._conn.execute(
            "CREATE TABLE IF NOT EXISTS drift (run_id TEXT, epoch INTEGER, name TEXT, drift_norm REAL)"
        )
        cls._conn.execute(
            "CREATE TABLE IF NOT EXISTS metrics (run_id TEXT, step INTEGER, epoch INTEGER, name TEXT, value REAL)"
        )
        cls._migrate_runs_columns()
        cls._conn.commit()

    @classmethod
    def _migrate_runs_columns(cls):
        cur = cls._conn.execute("PRAGMA table_info(runs)")
        cols = {row[1] for row in cur.fetchall()}
        if "name" not in cols:
            cls._conn.execute("ALTER TABLE runs ADD COLUMN name TEXT")
        if "tags" not in cols:
            cls._conn.execute("ALTER TABLE runs ADD COLUMN tags TEXT")

    @classmethod
    def insert_run(cls, run_id: str, framework: str, config: str, env: str):
        with cls._lock:
            cls._conn.execute(
                "INSERT INTO runs(run_id, ts, framework, config, env) VALUES (?, strftime('%s','now'), ?, ?, ?)",
                (run_id, framework, config, env),
            )
            cls._conn.commit()
        cls._notify("run_started", {"run_id": run_id, "framework": framework})

    @classmethod
    def insert_grad_stats_batch(cls, rows: List[Tuple[str, int, Optional[int], str, float, float, float]]):
        if not rows:
            return
        with cls._lock:
            cls._conn.executemany(
                "INSERT INTO grad_stats(run_id, step, epoch, name, norm, mean, max) VALUES (?,?,?,?,?,?,?)",
                rows,
            )
            cls._conn.commit()
        cls._notify("grad_stats", {"count": len(rows), "run_id": rows[0][0] if rows else None})

    @classmethod
    def insert_weight_updates_batch(cls, rows: List[Tuple[str, int, Optional[int], str, float]]):
        if not rows:
            return
        with cls._lock:
            cls._conn.executemany(
                "INSERT INTO weight_updates(run_id, step, epoch, name, update_norm) VALUES (?,?,?,?,?)",
                rows,
            )
            cls._conn.commit()
        cls._notify("weight_updates", {"count": len(rows), "run_id": rows[0][0] if rows else None})

    @classmethod
    def insert_alert(cls, run_id: str, step: int, epoch: Optional[int], type_: str, message: str, severity: str):
        with cls._lock:
            cls._conn.execute(
                "INSERT INTO alerts(run_id, step, epoch, type, message, severity) VALUES (?,?,?,?,?,?)",
                (run_id, step, epoch, type_, message, severity),
            )
            cls._conn.commit()
        try:
            import sys
            sys.stderr.write(f"[GradScope][{severity}] {type_}: {message} (step={step} epoch={epoch})\n")
        except Exception:
            pass
        cls._notify("alert", {"run_id": run_id, "step": step, "epoch": epoch, "type": type_, "message": message, "severity": severity})

    @classmethod
    def fetch_alerts(cls, run_id: str) -> List[Dict[str, Any]]:
        if cls._conn is None:
            cls.init()
        
        cursor = cls._conn.execute(
            "SELECT step, epoch, type, message, severity FROM alerts WHERE run_id=? ORDER BY step ASC",
            (run_id,)
        )
        return [
            {
                "step": step,
                "epoch": epoch,
                "type": type_,
                "message": msg,
                "severity": sev,
            }
            for step, epoch, type_, msg, sev in cursor.fetchall()
        ]

    @classmethod
    def insert_drift_batch(cls, rows: List[Tuple[str, int, str, float]]):

        if not rows:
            return
        with cls._lock: 
            cls._conn.executemany(
                "INSERT INTO drift(run_id, epoch, name, drift_norm) VALUES (?,?,?,?)",
                rows,
            )
            cls._conn.commit()
        cls._notify("drift", {"count": len(rows), "run_id": rows[0][0] if rows else None})

    @classmethod
    def fetch_grad_stats(cls, run_id: str, epoch: int):
        with cls._lock:
            cur = cls._conn.execute(
                "SELECT name, norm, mean, max FROM grad_stats WHERE run_id=? AND epoch=?",
                (run_id, epoch),
            )
            return cur.fetchall()

    @classmethod
    def insert_metric(cls, run_id: str, step: int, epoch: Optional[int], name: str, value: float):
        with cls._lock:
            cls._conn.execute(
                "INSERT INTO metrics(run_id, step, epoch, name, value) VALUES (?,?,?,?,?)",
                (run_id, step, epoch, name, value),
            )
            cls._conn.commit()
        cls._notify("metric", {"run_id": run_id, "step": step, "epoch": epoch, "name": name, "value": value})

    @classmethod
    def fetch_metrics(cls, run_id: str, name: str, limit: int = 100):
        with cls._lock:
            cur = cls._conn.execute(
                "SELECT step, epoch, value FROM metrics WHERE run_id=? AND name=? ORDER BY step DESC LIMIT ?",
                (run_id, name, limit),
            )
            return cur.fetchall()

    @classmethod
    def register_listener(cls, fn: Callable[[str, Dict], None]):
        cls._listeners.append(fn)

    @classmethod
    def _notify(cls, event: str, payload: Dict):
        for fn in list(cls._listeners):
            try:
                fn(event, payload)
            except Exception:
                pass
