from typing import Dict, List, Tuple, Optional

from .storage import Storage


def grad_diff(run_id: str, epoch_a: int, epoch_b: int) -> Dict[str, float]:
    a = Storage.fetch_grad_stats(run_id, epoch_a)
    b = Storage.fetch_grad_stats(run_id, epoch_b)
    da = {name: norm for name, norm, mean, maxv in a}
    db = {name: norm for name, norm, mean, maxv in b}
    keys = set(da.keys()) | set(db.keys())
    return {k: db.get(k, 0.0) - da.get(k, 0.0) for k in keys}


def grad_diff_summary(run_id: str, epoch_a: int, epoch_b: int, top_k: int = 5):
    delta = grad_diff(run_id, epoch_a, epoch_b)
    items = list(delta.items())
    items.sort(key=lambda x: x[1], reverse=True)
    inc = items[:top_k]
    dec = sorted(items, key=lambda x: x[1])[:top_k]
    vals = [v for _, v in items]
    mean_delta = sum(vals) / max(len(vals), 1) if vals else 0.0
    l2 = (sum(v * v for v in vals)) ** 0.5 if vals else 0.0
    return {"increases": inc, "decreases": dec, "mean_delta": mean_delta, "l2_delta": l2}


def grad_diff_cross_run(
    run_a: str,
    run_b: str,
    epoch_a: Optional[int] = None,
    epoch_b: Optional[int] = None,
) -> Dict[str, float]:
    ea = 0 if epoch_a is None else epoch_a
    eb = 0 if epoch_b is None else epoch_b
    a = Storage.fetch_grad_stats(run_a, ea)
    b = Storage.fetch_grad_stats(run_b, eb)
    da = {name: norm for name, norm, mean, maxv in a}
    db = {name: norm for name, norm, mean, maxv in b}
    keys = set(da.keys()) | set(db.keys())
    return {k: db.get(k, 0.0) - da.get(k, 0.0) for k in keys}


def grad_diff_filtered(
    run_id: str,
    epoch_a: int,
    epoch_b: int,
    min_norm: float = 0.0,
    name_contains: Optional[str] = None,
) -> Dict[str, float]:
    delta = grad_diff(run_id, epoch_a, epoch_b)
    out: Dict[str, float] = {}
    for name, v in delta.items():
        if name_contains is not None and name_contains not in name:
            continue
        if abs(v) < min_norm:
            continue
        out[name] = v
    return out


def grad_diff_ranked(
    run_id: str,
    epoch_a: int,
    epoch_b: int,
    top_k: int = 10,
    by_abs: bool = True,
) -> List[Tuple[str, float]]:
    delta = grad_diff(run_id, epoch_a, epoch_b)
    items = list(delta.items())
    if by_abs:
        items.sort(key=lambda x: abs(x[1]), reverse=True)
    else:
        items.sort(key=lambda x: x[1], reverse=True)
    return items[:top_k]
