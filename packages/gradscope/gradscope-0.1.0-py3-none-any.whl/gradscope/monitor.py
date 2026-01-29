import time
from typing import Any, Optional, Callable, Dict

from .registry import RunRegistry
from .backends.torch import TorchMonitor
from .backends.tf import TFMonitor


class GradScopeRun:
    def __init__(self, run_id: str, backend: Any, name: Optional[str] = None, tags: Optional[Dict[str, str]] = None, config: Optional[dict] = None):
        from .storage import Storage
        from .alerts import AlertRules
        from .utils import EMA as _EMA

        self.run_id = run_id
        self.backend = backend
        self.name = name
        self.tags = tags or {}
        self.config = config or {}
        self._handlers: list[Callable[[Dict], None]] = []
        self._metric_ema: Dict[str, Any] = {}
        self._ema_cls = _EMA
        self._rules = AlertRules()
        Storage.register_listener(self._on_event)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc is not None:
            reason = repr(exc)
            self.mark_failure(reason)
        self.close()
        return False

    def mark_epoch(self, epoch: int):
        self.backend.set_epoch(epoch)

    def log_metric(self, name: str, value: float, step: Optional[int] = None, epoch: Optional[int] = None):
        from .storage import Storage
        s = step if step is not None else getattr(self.backend, "step", 0)
        e = epoch if epoch is not None else getattr(self.backend, "epoch", None)
        ema_obj = self._metric_ema.get(name) or self._ema_cls(0.95)
        self._metric_ema[name] = ema_obj
        ema_val = ema_obj.update(value)
        Storage.insert_metric(self.run_id, s, e, name, value)
        self._rules.evaluate_metric(self.run_id, s, e, name, value, ema_val)

    def log_system_metrics(self, prefix: str = "sys"):
        from .utils import system_usage

        stats = system_usage()
        s = getattr(self.backend, "step", 0)
        e = getattr(self.backend, "epoch", None)
        for key, value in stats.items():
            if isinstance(value, (int, float)):
                self.log_metric(f"{prefix}.{key}", float(value), step=s, epoch=e)
            elif isinstance(value, (list, tuple)):
                for idx, v in enumerate(value):
                    try:
                        fv = float(v)
                    except Exception:
                        continue
                    self.log_metric(f"{prefix}.{key}.{idx}", fv, step=s, epoch=e)

    def add_alert_handler(self, fn: Callable[[Dict], None]):
        self._handlers.append(fn)

    def set_tag(self, key: str, value: str):
        self.tags[key] = value

    def mark_failure(self, reason: str):
        from .storage import Storage

        step = getattr(self.backend, "step", 0)
        epoch = getattr(self.backend, "epoch", None)
        Storage.insert_alert(self.run_id, step, epoch, "run_failure", reason, "critical")
        rules = getattr(self.backend, "rules", None)
        stats = getattr(self.backend, "last_grad_stats", None)
        if rules is not None and stats is not None:
            try:
                rules.attribute_failure(self.run_id, step, epoch, stats)
            except Exception:
                pass

    def close(self):
        self.backend.close()

    def summary(self) -> Dict:
        from .report import run_summary
        return run_summary(self.run_id)

    def _on_event(self, event: str, payload: Dict):
        if event == "alert":
            for fn in list(self._handlers):
                try:
                    fn(payload)
                except Exception:
                    pass


def attach(model: Any, optimizer: Any, framework: Optional[str] = None, config: Optional[dict] = None, name: Optional[str] = None, tags: Optional[Dict[str, str]] = None) -> GradScopeRun:
    if framework is None:
        framework = _infer_framework(model, optimizer)
    run_id = RunRegistry.start_run(framework=framework, config=config, name=name, tags=tags)
    if framework == "torch":
        backend = TorchMonitor(run_id, model, optimizer)
    elif framework == "tf":
        backend = TFMonitor(run_id, model, optimizer)
    else:
        raise ValueError("Unsupported framework")
    return GradScopeRun(run_id, backend, name=name, tags=tags, config=config)


def _infer_framework(model: Any, optimizer: Any) -> str:
    try:
        import torch
        if isinstance(optimizer, torch.optim.Optimizer):
            return "torch"
    except Exception:
        pass
    try:
        import tensorflow as tf
        if isinstance(optimizer, tf.keras.optimizers.Optimizer):
            return "tf"
    except Exception:
        pass
    raise ValueError("Unable to infer framework")
