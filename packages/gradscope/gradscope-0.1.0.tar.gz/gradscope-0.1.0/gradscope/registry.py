import json
import uuid
from typing import Optional, Dict

from .storage import Storage
from .utils import collect_env_info, get_device_info, get_framework_versions


class RunRegistry:
    @staticmethod
    def start_run(framework: str, config: Optional[dict] = None, name: Optional[str] = None, tags: Optional[Dict[str, str]] = None) -> str:
        run_id = str(uuid.uuid4())
        env = collect_env_info(framework)
        env["device"] = get_device_info()
        env["framework_versions"] = get_framework_versions()
        meta = dict(config or {})
        if name:
            meta["name"] = name
        if tags:
            meta["tags"] = tags
        Storage.init()
        Storage.insert_run(run_id, framework, json.dumps(meta), json.dumps(env))
        return run_id

    @staticmethod
    def update_tags(run_id: str, tags: Dict[str, str]) -> None:
        Storage.init()
        conn = Storage._conn
        cur = conn.execute("SELECT config FROM runs WHERE run_id=?", (run_id,))
        row = cur.fetchone()
        if row is None:
            return
        cfg = json.loads(row[0] or "{}")
        existing = cfg.get("tags", {})
        existing.update(tags)
        cfg["tags"] = existing
        conn.execute("UPDATE runs SET config=? WHERE run_id=?", (json.dumps(cfg), run_id))
        conn.commit()

    @staticmethod
    def get_run_config(run_id: str) -> Optional[dict]:
        Storage.init()
        conn = Storage._conn
        cur = conn.execute("SELECT config FROM runs WHERE run_id=?", (run_id,))
        row = cur.fetchone()
        if row is None:
            return None
        return json.loads(row[0] or "{}")
