import os
import types

from gradscope import utils


def test_collect_env_info_fields(monkeypatch):
    monkeypatch.setattr(utils, "_get_git_hash", lambda: "deadbeef")
    env = utils.collect_env_info("torch")
    assert env["framework"] == "torch"
    assert "python" in env and isinstance(env["python"], str)
    assert env["git"] == "deadbeef"
    assert "git_branch" in env
    assert "git_dirty" in env


def test_ema_updates_and_initial_none():
    ema = utils.EMA(alpha=0.5)
    assert ema.value is None
    v1 = ema.update(2.0)
    assert v1 == 2.0
    v2 = ema.update(4.0)
    assert v2 == 3.0


def test_rolling_window_mean_std():
    win = utils.RollingWindow(size=3)
    win.add(1.0)
    win.add(2.0)
    win.add(3.0)
    mu, sd = win.mean_std()
    assert mu == 2.0
    assert sd > 0


def test_rate_limiter_basic():
    rl = utils.RateLimiter(steps=2)
    assert rl.allow("k", 0)
    assert not rl.allow("k", 1)
    assert rl.allow("k", 2)


def test_set_seed_and_seed_scope_restores_state():
    utils.set_seed(123)
    import random

    a = random.random()
    with utils.seed_scope(123):
        b1 = random.random()
        utils.set_seed(123)
        b2 = random.random()
        assert b1 == b2


def test_serialize_value_basic_types_and_unknown():
    assert utils.serialize_value(1) == 1
    assert utils.serialize_value(1.5) == 1.5
    assert utils.serialize_value("x") == "x"
    assert utils.serialize_value(True) is True
    x = types.SimpleNamespace()
    s = utils.serialize_value(x)
    assert isinstance(s, str)


def test_get_device_info_and_framework_versions(monkeypatch):
    import builtins

    info = utils.get_device_info()
    assert "cuda" in info and "gpus" in info and "tf_gpus" in info

    v = utils.get_framework_versions()
    assert isinstance(v, dict)


def test_format_size_and_time_helpers():
    out = utils.format_size(1024)
    assert "KB" in out
    assert isinstance(utils.now_ns(), int)
    assert isinstance(utils.monotonic_ns(), int)


def test_ensure_dir_creates(tmp_path):
    p = tmp_path / "subdir"
    utils.ensure_dir(str(p))
    assert os.path.isdir(p)


def test_sleep_ms_executes_quickly():
    utils.sleep_ms(1)


def test_system_usage_structure():
    info = utils.system_usage()
    assert "cuda" in info
    assert "gpu_mem" in info
    assert "rss" in info
    assert "cpu_percent" in info


def test_check_dependency_self_and_missing():
    info = utils.check_dependency("math")
    assert info["available"] is True
    missing = utils.check_dependency("definitely_missing_package_name_xyz")
    assert missing["available"] is False
