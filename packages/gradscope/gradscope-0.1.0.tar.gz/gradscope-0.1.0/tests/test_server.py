import pytest
import sys


def _has_server_deps():
    try:
        import fastapi  # noqa: F401
        import uvicorn  # noqa: F401
    except ImportError:
        return False
    return True


@pytest.mark.skipif(not _has_server_deps(), reason="server dependencies not installed")
def test_create_app_and_index():
    from gradscope.server import create_app
    app = create_app()
    assert app.title == "GradScope"

    from fastapi.testclient import TestClient
    client = TestClient(app)
    r = client.get("/")
    assert r.status_code == 200
    assert "GradScope Dashboard" in r.text


def test_create_app_requires_fastapi(monkeypatch):
    import builtins

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "fastapi":
            raise ImportError("no fastapi")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    from gradscope import server

    with pytest.raises(RuntimeError) as exc:
        server.create_app()
    assert "FastAPI is required" in str(exc.value)


def test_serve_requires_uvicorn(monkeypatch):
    import builtins

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "uvicorn":
            raise ImportError("no uvicorn")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    from gradscope import server

    with pytest.raises(RuntimeError) as exc:
        server.serve()
    assert "uvicorn is required" in str(exc.value)
