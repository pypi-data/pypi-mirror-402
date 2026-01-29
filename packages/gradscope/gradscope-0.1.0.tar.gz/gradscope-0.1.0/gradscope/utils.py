import os
import platform
import random
import time
import math
from typing import Dict, Any, Optional, List


def collect_env_info(framework: str) -> Dict:
    git_hash = _get_git_hash()
    git_branch, git_dirty = _get_git_branch_and_dirty()
    return {
        "framework": framework,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "hostname": platform.node(),
        "pid": os.getpid(),
        "time": int(time.time()),
        "git": git_hash,
        "git_branch": git_branch,
        "git_dirty": git_dirty,
    }


def _get_git_hash() -> str:
    try:
        import subprocess
        out = subprocess.check_output(["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL)
        return out.decode().strip()
    except Exception:
        return ""


def _get_git_branch_and_dirty() -> tuple[str, bool]:
    try:
        import subprocess
        branch_out = subprocess.check_output([
            "git",
            "rev-parse",
            "--abbrev-ref",
            "HEAD",
        ], stderr=subprocess.DEVNULL)
        branch = branch_out.decode().strip()
        status_out = subprocess.check_output([
            "git",
            "status",
            "--porcelain",
        ], stderr=subprocess.DEVNULL)
        dirty = bool(status_out.decode().strip())
        return branch, dirty
    except Exception:
        return "", False


def set_seed(seed: int):
    try:
        import numpy as np
        np.random.seed(seed)
    except Exception:
        pass
    random.seed(seed)
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except Exception:
        pass
    try:
        import tensorflow as tf
        tf.random.set_seed(seed)
    except Exception:
        pass


class seed_scope:
    def __init__(self, seed: int):
        self.seed = seed
        self._py_state = None
        self._np_state = None
        self._torch_cpu_state = None
        self._torch_cuda_states = None

    def __enter__(self):
        self._py_state = random.getstate()
        try:
            import numpy as np
            self._np_state = np.random.get_state()
        except Exception:
            self._np_state = None
        try:
            import torch
            self._torch_cpu_state = torch.random.get_rng_state()
            if torch.cuda.is_available():
                self._torch_cuda_states = [torch.cuda.get_rng_state(i) for i in range(torch.cuda.device_count())]
        except Exception:
            self._torch_cpu_state = None
            self._torch_cuda_states = None
        set_seed(self.seed)
        return self

    def __exit__(self, exc_type, exc, tb):
        if self._py_state is not None:
            random.setstate(self._py_state)
        try:
            import numpy as np
            if self._np_state is not None:
                np.random.set_state(self._np_state)
        except Exception:
            pass
        try:
            import torch
            if self._torch_cpu_state is not None:
                torch.random.set_rng_state(self._torch_cpu_state)
            if self._torch_cuda_states is not None and torch.cuda.is_available():
                for i, st in enumerate(self._torch_cuda_states):
                    torch.cuda.set_rng_state(st, device=i)
        except Exception:
            pass


def get_device_info() -> Dict:
    info = {"cuda": False, "gpus": 0, "tf_gpus": 0}
    try:
        import torch
        info["cuda"] = torch.cuda.is_available()
        info["gpus"] = torch.cuda.device_count() if info["cuda"] else 0
    except Exception:
        pass
    try:
        import tensorflow as tf
        info["tf_gpus"] = len(tf.config.list_physical_devices("GPU"))
    except Exception:
        pass
    return info


def get_framework_versions() -> Dict:
    v = {}
    try:
        import torch
        v["torch"] = getattr(torch, "__version__", "")
    except Exception:
        pass
    try:
        import tensorflow as tf
        v["tensorflow"] = getattr(tf, "__version__", "")
    except Exception:
        pass
    return v


class EMA:
    def __init__(self, alpha: float = 0.95):
        self.alpha = alpha
        self.value: Optional[float] = None

    def update(self, x: float) -> float:
        self.value = x if self.value is None else self.alpha * self.value + (1 - self.alpha) * x
        return self.value


class RollingWindow:
    def __init__(self, size: int = 20):
        self.size = size
        self.buf: List[float] = []

    def add(self, x: float):
        self.buf.append(x)
        if len(self.buf) > self.size:
            del self.buf[0]

    def mean_std(self):
        if not self.buf:
            return 0.0, 0.0
        mu = sum(self.buf) / len(self.buf)
        var = sum((v - mu) ** 2 for v in self.buf) / len(self.buf)
        return mu, math.sqrt(var)


class RateLimiter:
    def __init__(self, steps: int = 50):
        self.steps = steps
        self.last: Dict[str, int] = {}

    def allow(self, key: str, step: int) -> bool:
        prev = self.last.get(key)
        if prev is None or step - prev >= self.steps:
            self.last[key] = step
            return True
        return False


def serialize_value(x: Any) -> Any:
    try:
        import torch
        if isinstance(x, torch.Tensor):
            if x.numel() == 1:
                return x.detach().cpu().item()
            return x.detach().cpu().tolist()
    except Exception:
        pass
    try:
        import numpy as np
        if isinstance(x, np.ndarray):
            if x.size == 1:
                return float(x.reshape(-1)[0])
            return x.tolist()
    except Exception:
        pass
    if isinstance(x, (int, float, str, bool)) or x is None:
        return x
    try:
        return float(x)
    except Exception:
        return str(x)


def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def format_size(n: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    s = float(n)
    i = 0
    while s >= 1024 and i < len(units) - 1:
        s /= 1024
        i += 1
    return f"{s:.2f} {units[i]}"


def now_ns() -> int:
    try:
        return time.time_ns()
    except AttributeError:
        return int(time.time() * 1e9)


def monotonic_ns() -> int:
    try:
        return time.monotonic_ns()
    except AttributeError:
        return int(time.monotonic() * 1e9)


def sleep_ms(ms: int):
    time.sleep(ms / 1000.0)


def system_usage() -> Dict[str, Any]:
    info: Dict[str, Any] = {}
    try:
        import psutil
        p = psutil.Process(os.getpid())
        info["rss"] = p.memory_info().rss
        info["cpu_percent"] = p.cpu_percent(interval=0.0)
    except Exception:
        info["rss"] = None
        info["cpu_percent"] = None
    try:
        import torch
        if torch.cuda.is_available():
            info["cuda"] = True
            info["gpu_mem"] = [torch.cuda.memory_allocated(i) for i in range(torch.cuda.device_count())]
        else:
            info["cuda"] = False
            info["gpu_mem"] = []
    except Exception:
        try:
            import tensorflow as tf
            gpus = tf.config.list_physical_devices("GPU")
            info["cuda"] = bool(gpus)
            info["gpu_mem"] = []
        except Exception:
            info["cuda"] = False
            info["gpu_mem"] = []
    return info


def check_dependency(name: str) -> Dict[str, Any]:
    try:
        mod = __import__(name)
        ver = getattr(mod, "__version__", "")
        return {"available": True, "version": ver}
    except Exception:
        return {"available": False, "version": ""}
