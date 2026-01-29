from typing import List, Tuple, Optional, Dict
from .utils import RollingWindow, EMA, RateLimiter
from .storage import Storage
from .config import get_config


class AlertRules:
    def __init__(
        self,
        vanish_thresh: Optional[float] = None,
        explode_thresh: Optional[float] = None,
        spike_factor: Optional[float] = None,
        metric_spike_factor: Optional[float] = None,
        window_size: Optional[int] = None,
        rate_limit_steps: Optional[int] = None,
        z_thresh: Optional[float] = None,
        cv_thresh: Optional[float] = None,
        per_layer_thresholds: Optional[Dict[str, Tuple[float, float]]] = None,
    ):
        cfg = get_config()
        self.vanish_thresh = cfg.vanish_thresh if vanish_thresh is None else vanish_thresh
        self.explode_thresh = cfg.explode_thresh if explode_thresh is None else explode_thresh
        self.spike_factor = cfg.spike_factor if spike_factor is None else spike_factor
        self.metric_spike_factor = cfg.metric_spike_factor if metric_spike_factor is None else metric_spike_factor
        self.window_size = cfg.window_size if window_size is None else window_size
        self.rate_limit_steps = cfg.rate_limit_steps if rate_limit_steps is None else rate_limit_steps
        self.z_thresh = cfg.z_thresh if z_thresh is None else z_thresh
        self.cv_thresh = cfg.cv_thresh if cv_thresh is None else cv_thresh
        self.per_layer_thresholds = per_layer_thresholds or {}
        self._grad_ema: Dict[str, EMA] = {}
        self._grad_win: Dict[str, RollingWindow] = {}
        self._upd_ema: Dict[str, EMA] = {}
        self._upd_win: Dict[str, RollingWindow] = {}
        self._metric_ema: Dict[str, EMA] = {}
        self._metric_win: Dict[str, RollingWindow] = {}
        self._rate = RateLimiter(rate_limit_steps)

    def evaluate_gradients(self, run_id: str, step: int, epoch: Optional[int], stats: List[Tuple[str, float, float, float]], ema: Optional[float]):
        for name, norm, mean, maxv in stats:
            vt, et = self._layer_thresholds(name)
            win = self._grad_win.get(name) or RollingWindow(self.window_size)
            self._grad_win[name] = win
            ema_obj = self._grad_ema.get(name) or EMA(0.95)
            prev = ema_obj.value
            ema_obj.update(norm)
            self._grad_ema[name] = ema_obj
            win.add(norm)
            if norm < vt and self._rate.allow(f"grad_vanish:{name}", step):
                Storage.insert_alert(run_id, step, epoch, "vanish_gradient", name, "high")
            elif norm > et and self._rate.allow(f"grad_explode:{name}", step):
                Storage.insert_alert(run_id, step, epoch, "explode_gradient", name, "critical")
            mu, sd = win.mean_std()
            if sd > 1e-12:
                z = abs((norm - mu) / sd)
                if z > self.z_thresh and self._rate.allow(f"grad_z_spike:{name}", step):
                    Storage.insert_alert(run_id, step, epoch, "grad_z_spike", name, "warning")
            if prev is not None and norm > prev * self.spike_factor and self._rate.allow(f"grad_layer_spike:{name}", step):
                Storage.insert_alert(run_id, step, epoch, "grad_layer_spike", name, "warning")
        if stats:
            norms = [s[1] for s in stats]
            mu = sum(norms) / max(len(norms), 1)
            sd = (sum((v - mu) ** 2 for v in norms) / max(len(norms), 1)) ** 0.5 if norms else 0.0
            if mu > 0 and sd / mu > self.cv_thresh and self._rate.allow("grad_cv_instability", step):
                Storage.insert_alert(run_id, step, epoch, "grad_cv_instability", "layers", "warning")
        if ema is not None:
            avg_norm = sum(s[1] for s in stats) / max(len(stats), 1)
            if avg_norm > ema * self.spike_factor and self._rate.allow("instability_spike", step):
                Storage.insert_alert(run_id, step, epoch, "instability_spike", "avg_grad_norm", "warning")

    def attribute_failure(self, run_id: str, step: int, epoch: Optional[int], stats: List[Tuple[str, float, float, float]]):
        if not stats:
            Storage.insert_alert(run_id, step, epoch, "failure_attribution", "no_gradients", "info")
            return
        max_entry = max(stats, key=lambda x: x[1])
        Storage.insert_alert(run_id, step, epoch, "failure_attribution", f"gradient_issue:{max_entry[0]}", "info")

    def evaluate_metric(self, run_id: str, step: int, epoch: Optional[int], name: str, value: float, ema: Optional[float]):
        if value != value:
            Storage.insert_alert(run_id, step, epoch, "metric_nan", name, "critical")
            return
        if value == float("inf") or value == float("-inf"):
            Storage.insert_alert(run_id, step, epoch, "metric_inf", name, "critical")
            return
        if ema is not None and value > ema * self.metric_spike_factor and self._rate.allow(f"metric_spike:{name}", step):
            Storage.insert_alert(run_id, step, epoch, "metric_spike", name, "warning")
        win = self._metric_win.get(name) or RollingWindow(self.window_size)
        self._metric_win[name] = win
        win.add(value)
        mu, sd = win.mean_std()
        if sd > 1e-12:
            z = abs((value - mu) / sd)
            if z > self.z_thresh and self._rate.allow(f"metric_z_spike:{name}", step):
                Storage.insert_alert(run_id, step, epoch, "metric_z_spike", name, "warning")
        if len(win.buf) >= self.window_size:
            rng = max(win.buf) - min(win.buf)
            if rng < 1e-8 and self._rate.allow(f"metric_plateau:{name}", step):
                Storage.insert_alert(run_id, step, epoch, "metric_plateau", name, "info")

    def evaluate_weight_updates(self, run_id: str, step: int, epoch: Optional[int], updates: List[Tuple[str, float]]):
        for name, u in updates:
            win = self._upd_win.get(name) or RollingWindow(self.window_size)
            self._upd_win[name] = win
            ema = self._upd_ema.get(name) or EMA(0.95)
            prev = ema.value
            ema.update(u)
            self._upd_ema[name] = ema
            win.add(u)
            mu, sd = win.mean_std()
            if prev is not None and u > prev * self.spike_factor and self._rate.allow(f"update_spike:{name}", step):
                Storage.insert_alert(run_id, step, epoch, "update_spike", name, "warning")
            if prev is not None and u < prev * 0.1 and self._rate.allow(f"update_stall:{name}", step):
                Storage.insert_alert(run_id, step, epoch, "update_stall", name, "info")
            if sd > 1e-12:
                z = abs((u - mu) / sd)
                if z > self.z_thresh and self._rate.allow(f"update_z_spike:{name}", step):
                    Storage.insert_alert(run_id, step, epoch, "update_z_spike", name, "warning")


    def _layer_thresholds(self, name: str):
        th = self.per_layer_thresholds.get(name)
        if th:
            return th[0], th[1]
        return self.vanish_thresh, self.explode_thresh

    
