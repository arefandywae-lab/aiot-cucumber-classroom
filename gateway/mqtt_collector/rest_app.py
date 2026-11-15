import hashlib
import hmac
import json
import os
import time
from urllib.parse import parse_qsl

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
import uvicorn

import ai_helpers
import sqlite3
from contextlib import closing

app = FastAPI()
# The web UI on GitHub Pages is served from another origin, so allow cross-origin reads.
app.add_middleware(CORSMiddleware, allow_origins=[o.strip() for o in os.environ.get("CORS_ORIGINS", "https://arefandywae-lab.github.io").split(",") if o.strip()], allow_methods=["GET", "POST"], allow_headers=["*"])

with closing(sqlite3.connect("data.db")) as conn:
    sqlcmd = ("CREATE TABLE IF NOT EXISTS data ("
              "_id INTEGER PRIMARY KEY AUTOINCREMENT, "
              "node INTEGER, "
              "value REAL, "
              "ts TEXT DEFAULT (datetime('now')));")
    conn.execute(sqlcmd)
    conn.commit()

# Cucumber node ids -> (display name, unit). See include/Config.h in the
# cucumber_demo05 firmware project for the matching NODE_* defines.
NODE_INFO = {
    1: ("BMP280 Temperature", "°C"),
    2: ("BMP280 Pressure", "hPa"),
    3: ("HTS221 Temperature", "°C"),
    4: ("HTS221 Humidity", "%"),
}


@app.get("/items/{item_id}")
def read_item(item_id: int):
    with closing(sqlite3.connect("data.db")) as conn:
        sqlcmd = 'SELECT value, ts FROM data WHERE node = ? ORDER BY _id DESC LIMIT 1;'
        row = conn.execute(sqlcmd, (item_id,)).fetchone()
    if row is None:
        return {"item_id": item_id}
    return {"item_id": item_id, "value": row[0], "ts": row[1]}


@app.get("/log")
def read_log(limit: int = 30):
    limit = max(1, min(limit, 500))
    with closing(sqlite3.connect("data.db")) as conn:
        sqlcmd = 'SELECT _id, node, value, ts FROM data ORDER BY _id DESC LIMIT ?;'
        rows = conn.execute(sqlcmd, (limit,)).fetchall()
    # Return oldest-first so the dashboard can just append to the bottom.
    rows.reverse()
    return [{"id": r[0], "node": r[1], "value": r[2], "ts": r[3]} for r in rows]


@app.get("/api/summary")
def summary(minutes: int = 30):
    """Latest value of every node plus a time series for the Mini App charts."""
    minutes = max(1, min(minutes, 24 * 60))
    with closing(sqlite3.connect("data.db")) as conn:
        latest = {}
        for node in NODE_INFO:
            row = conn.execute("SELECT value, ts FROM data WHERE node = ? ORDER BY _id DESC LIMIT 1;",
                               (node,)).fetchone()
            if row:
                latest[node] = {"value": row[0], "ts": row[1]}
        rows = conn.execute("SELECT node, value, ts FROM data WHERE ts >= datetime('now', ?) "
                            "AND node IN (3, 4) ORDER BY _id;", (f"-{minutes} minutes",)).fetchall()
    series = {3: [], 4: []}
    for node, value, ts in rows:
        series[node].append([ts, value])
    return {"latest": latest, "series": series, "server_time": time.time()}


def check_init_data(init_data: str, token: str, max_age: int = 86400):
    """Validate Telegram Mini App initData (HMAC-SHA256 per the Mini Apps docs). Returns user dict."""
    fields = dict(parse_qsl(init_data, keep_blank_values=True))
    got_hash = fields.pop("hash", "")
    check = "\n".join(f"{k}={v}" for k, v in sorted(fields.items()))
    secret = hmac.new(b"WebAppData", token.encode(), hashlib.sha256).digest()
    want = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
    if not got_hash or not hmac.compare_digest(want, got_hash):
        raise ValueError("bad signature")
    if time.time() - int(fields.get("auth_date", 0)) > max_age:
        raise ValueError("initData too old")
    return json.loads(fields.get("user", "{}"))


@app.post("/api/verify")
async def verify(request: Request):
    """The Mini App posts its initData here; only data signed by Telegram for our bot passes."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        raise HTTPException(503, "bot token not configured")
    body = await request.json()
    try:
        user = check_init_data(body.get("initData", ""), token)
    except ValueError as exc:
        raise HTTPException(401, str(exc))
    return {"ok": True, "user": {"id": user.get("id"), "first_name": user.get("first_name")}}


def _series(minutes):
    with closing(sqlite3.connect("data.db")) as conn:
        rows = conn.execute("SELECT node, value, ts FROM data WHERE ts >= datetime('now', ?) "
                            "AND node IN (3, 4) ORDER BY _id;", (f"-{max(1, min(minutes, 1440))} minutes",)).fetchall()
    series = {3: [], 4: []}
    for node, value, ts in rows:
        series[node].append([ts, value])
    return series


def _latest():
    with closing(sqlite3.connect("data.db")) as conn:
        out = {}
        for node in NODE_INFO:
            row = conn.execute("SELECT value, ts FROM data WHERE node = ? ORDER BY _id DESC LIMIT 1;",
                               (node,)).fetchone()
            if row:
                out[node] = {"value": row[0], "ts": row[1]}
    return out


@app.get("/api/anomaly")
def anomaly(minutes: int = 60):
    """AI #1 - statistics: is the recent temperature / humidity unusual compared with earlier?"""
    return {"minutes": minutes, "results": ai_helpers.detect_anomalies(_series(minutes))}


_ask_times = []  # timestamps of recent /api/ask calls (simple global rate limit)
ASK_LIMIT_PER_MIN = int(os.environ.get("ASK_LIMIT_PER_MIN", "12"))


@app.post("/api/ask")
async def ask(request: Request):
    """AI #2 - chat about the sensors. Uses an LLM (OLLAMA_URL) if available, otherwise simple rules."""
    now = time.time()
    _ask_times[:] = [x for x in _ask_times if now - x < 60]
    if len(_ask_times) >= ASK_LIMIT_PER_MIN:
        raise HTTPException(429, "ถามถี่เกินไป รอสักครู่แล้วลองใหม่")
    _ask_times.append(now)
    body = await request.json()
    question = str(body.get("question", "")).strip()[:300]
    if not question:
        raise HTTPException(400, "question is empty")
    anomalies = ai_helpers.detect_anomalies(_series(60))
    return ai_helpers.answer_question(question, _latest(), anomalies)


@app.get("/app", response_class=HTMLResponse)
def mini_app():
    return FileResponse("miniapp.html", media_type="text/html")


@app.get("/", response_class=HTMLResponse)
def dashboard():
    return DASHBOARD_HTML


DASHBOARD_HTML = """<!doctype html>
<html lang="th">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Cucumber Environment Dashboard</title>
<style>
  :root { color-scheme: light dark; }
  body {
    margin: 0; padding: 24px; box-sizing: border-box;
    font-family: -apple-system, "Segoe UI", Sarabun, sans-serif;
    background: #0f172a; color: #e2e8f0;
  }
  h1 { font-size: 1.3rem; margin: 0 0 4px; }
  .subtitle { color: #94a3b8; font-size: 0.85rem; margin-bottom: 20px; }
  .grid {
    display: grid; gap: 14px;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    margin-bottom: 24px;
  }
  .card {
    background: #1e293b; border-radius: 12px; padding: 16px 18px;
    border: 1px solid #334155;
  }
  .card .name { font-size: 0.8rem; color: #94a3b8; margin-bottom: 8px; }
  .card .value { font-size: 2rem; font-weight: 700; line-height: 1; }
  .card .unit { font-size: 1rem; color: #94a3b8; margin-left: 4px; }
  .card .age { font-size: 0.72rem; color: #64748b; margin-top: 8px; }
  .card.stale { opacity: 0.45; }
  .panel {
    background: #1e293b; border-radius: 12px; border: 1px solid #334155;
    overflow: hidden;
  }
  .panel-header {
    padding: 10px 16px; border-bottom: 1px solid #334155;
    font-size: 0.85rem; color: #94a3b8; display: flex;
    justify-content: space-between; align-items: center;
  }
  .dot {
    width: 8px; height: 8px; border-radius: 50%; background: #22c55e;
    display: inline-block; margin-right: 6px;
    animation: pulse 1.5s ease-in-out infinite;
  }
  @keyframes pulse { 50% { opacity: 0.3; } }
  #log {
    font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
    font-size: 0.78rem; padding: 12px 16px; height: 320px;
    overflow-y: auto; white-space: pre;
  }
  #log div { padding: 1px 0; }
  #log .node1 { color: #38bdf8; }
  #log .node2 { color: #fbbf24; }
  #log .node3 { color: #f472b6; }
  #log .node4 { color: #4ade80; }
</style>
</head>
<body>
  <h1>&#127807; Cucumber Environment Dashboard</h1>
  <div class="subtitle">BMP280 + HTS221 &rarr; MQTT &rarr; Docker &rarr; REST &mdash; อัปเดตอัตโนมัติทุก 2 วินาที</div>

  <div class="grid" id="cards"></div>

  <div class="panel">
    <div class="panel-header">
      <span><span class="dot"></span>Live feed (เหมือน Serial Monitor)</span>
      <span id="log-count"></span>
    </div>
    <div id="log">รอข้อมูลจากบอร์ด...</div>
  </div>

<script>
const NODES = {
  1: {name: "BMP280 Temperature", unit: "°C"},
  2: {name: "BMP280 Pressure",    unit: "hPa"},
  3: {name: "HTS221 Temperature", unit: "°C"},
  4: {name: "HTS221 Humidity",    unit: "%"},
};

const cardsEl = document.getElementById('cards');
for (const id of Object.keys(NODES)) {
  const c = document.createElement('div');
  c.className = 'card';
  c.id = 'card-' + id;
  c.innerHTML = `
    <div class="name">${NODES[id].name}</div>
    <div><span class="value" id="val-${id}">&ndash;</span><span class="unit">${NODES[id].unit}</span></div>
    <div class="age" id="age-${id}">ยังไม่มีข้อมูล</div>`;
  cardsEl.appendChild(c);
}

// SQLite stores ts as UTC ("YYYY-MM-DD HH:MM:SS"); mark it explicitly as
// UTC ("Z" suffix) so the browser converts it to the viewer's local time
// instead of misreading it as already-local.
function parseUtc(ts) {
  return new Date(ts.replace(' ', 'T') + 'Z');
}

function timeAgo(ts) {
  if (!ts) return "ยังไม่มีข้อมูล";
  const secs = Math.max(0, Math.round((Date.now() - parseUtc(ts).getTime()) / 1000));
  if (secs < 60) return secs + " วินาทีที่แล้ว";
  return Math.round(secs / 60) + " นาทีที่แล้ว";
}

async function pollCards() {
  for (const id of Object.keys(NODES)) {
    try {
      const r = await fetch(`/items/${id}`);
      const data = await r.json();
      const card = document.getElementById('card-' + id);
      const valEl = document.getElementById('val-' + id);
      const ageEl = document.getElementById('age-' + id);
      if (data.value !== undefined) {
        valEl.textContent = Number(data.value).toFixed(2);
        ageEl.textContent = "อัปเดต " + timeAgo(data.ts);
        const secs = (Date.now() - parseUtc(data.ts).getTime()) / 1000;
        card.classList.toggle('stale', secs > 15);
      }
    } catch (e) { /* ignore transient errors */ }
  }
}

let lastLogId = 0;
async function pollLog() {
  try {
    const r = await fetch('/log?limit=40');
    const rows = await r.json();
    const logEl = document.getElementById('log');
    const atBottom = logEl.scrollTop + logEl.clientHeight >= logEl.scrollHeight - 20;
    let newRows = rows.filter(row => row.id > lastLogId);
    if (lastLogId === 0) newRows = rows; // first load: show existing history
    for (const row of newRows) {
      const info = NODES[row.node] || {name: 'node' + row.node, unit: ''};
      const line = document.createElement('div');
      line.className = 'node' + row.node;
      const localTime = parseUtc(row.ts).toLocaleTimeString('th-TH', {hour12: false});
      line.textContent = `[${localTime}] ${info.name.padEnd(20)} = ${Number(row.value).toFixed(2)} ${info.unit}`;
      logEl.appendChild(line);
      lastLogId = Math.max(lastLogId, row.id);
    }
    while (logEl.children.length > 200) logEl.removeChild(logEl.firstChild);
    if (atBottom) logEl.scrollTop = logEl.scrollHeight;
    document.getElementById('log-count').textContent = rows.length ? `#${lastLogId}` : '';
  } catch (e) { /* ignore transient errors */ }
}

pollCards(); pollLog();
setInterval(pollCards, 2000);
setInterval(pollLog, 2000);
</script>
</body>
</html>"""


if __name__ == "__main__":
    uvicorn.run("rest_app:app", host="0.0.0.0", port=5000, reload=True)
