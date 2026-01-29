from typing import Any
from contextlib import asynccontextmanager


def create_app() -> Any:
    try:
        from fastapi import FastAPI, APIRouter, HTTPException
        from fastapi.responses import HTMLResponse
    except Exception as e:
        raise RuntimeError("FastAPI is required for gradscope.server. Install fastapi.") from e

    from .storage import Storage
    from .api import include_routes

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        Storage.init()
        yield

    app = FastAPI(title="GradScope", version="0.1.0", lifespan=lifespan)

    include_routes(app, APIRouter, HTTPException)

    @app.get("/", response_class=HTMLResponse)
    async def index():
        return """<!doctype html>
<html>
<head>
<meta charset=\"utf-8\">
<title>GradScope Dashboard</title>
<style>
body { font-family: system-ui, -apple-system, BlinkMacSystemFont, sans-serif; margin: 16px; }
h1 { font-size: 20px; margin-bottom: 8px; }
select, button { margin: 4px 0; }
pre { background: #111; color: #eee; padding: 8px; overflow: auto; }
.row { display: flex; gap: 16px; flex-wrap: wrap; }
.panel { flex: 1 1 320px; border: 1px solid #ccc; padding: 8px; border-radius: 4px; }
</style>
</head>
<body>
<h1>GradScope Dashboard</h1>
<div>
<label for=\"run-select\">Run:</label>
<select id=\"run-select\"></select>
<button id=\"refresh-runs\">Refresh runs</button>
</div>
<div class=\"row\">
<div class=\"panel\">
<h2>Summary</h2>
<pre id=\"summary\">Select a run.</pre>
</div>
<div class=\"panel\">
<h2>Diagnostics</h2>
<pre id=\"diagnostics\"></pre>
</div>
</div>
<div class=\"row\">
<div class=\"panel\">
<h2>Loss</h2>
<pre id=\"loss\"></pre>
</div>
<div class=\"panel\">
<h2>System metrics</h2>
<pre id=\"system\"></pre>
</div>
</div>
<script>
async function fetchJSON(path) {
  const res = await fetch(path);
  if (!res.ok) throw new Error(await res.text());
  return await res.json();
}

async function loadRuns() {
  const sel = document.getElementById('run-select');
  sel.innerHTML = '';
  let runs = [];
  try {
    runs = await fetchJSON('/runs?limit=50');
  } catch (e) {
    console.error(e);
    return;
  }
  for (const r of runs) {
    const opt = document.createElement('option');
    opt.value = r.run_id;
    opt.textContent = r.config && r.config.name ? r.config.name + ' (' + r.run_id + ')' : r.run_id;
    sel.appendChild(opt);
  }
  if (runs.length) {
    sel.value = runs[0].run_id;
    await loadRunDetails();
  }
}

async function loadRunDetails() {
  const sel = document.getElementById('run-select');
  const runId = sel.value;
  if (!runId) return;
  try {
    const summary = await fetchJSON('/runs/' + encodeURIComponent(runId) + '/summary');
    document.getElementById('summary').textContent = JSON.stringify(summary, null, 2);
  } catch (e) {
    document.getElementById('summary').textContent = String(e);
  }
  try {
    const diag = await fetchJSON('/runs/' + encodeURIComponent(runId) + '/diagnostics');
    document.getElementById('diagnostics').textContent = JSON.stringify(diag, null, 2);
  } catch (e) {
    document.getElementById('diagnostics').textContent = String(e);
  }
  try {
    const loss = await fetchJSON('/runs/' + encodeURIComponent(runId) + '/metrics/loss');
    document.getElementById('loss').textContent = JSON.stringify(loss.slice(-50), null, 2);
  } catch (e) {
    document.getElementById('loss').textContent = 'No loss history';
  }
  try {
    const sys = await fetchJSON('/runs/' + encodeURIComponent(runId) + '/metrics/sys.cpu_percent');
    const rss = await fetchJSON('/runs/' + encodeURIComponent(runId) + '/metrics/sys.rss');
    document.getElementById('system').textContent = JSON.stringify({ cpu: sys.slice(-20), rss: rss.slice(-20) }, null, 2);
  } catch (e) {
    document.getElementById('system').textContent = 'No system metrics; call run.log_system_metrics().';
  }
}

document.getElementById('run-select').addEventListener('change', loadRunDetails);
document.getElementById('refresh-runs').addEventListener('click', loadRuns);

loadRuns();
</script>
</body>
</html>"""

    return app


def serve(host: str = "127.0.0.1", port: int = 8000):  # pragma: no cover
    try:
        import uvicorn
    except Exception as e:
        raise RuntimeError("uvicorn is required to run gradscope.server. Install uvicorn.") from e

    app = create_app()
    uvicorn.run(app, host=host, port=port)
