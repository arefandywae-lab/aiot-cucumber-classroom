"""Telegram bot for the Cucumber environment demo (3rd process in the mqtt_collector container).

Features (tagged F1..F9 in the section comments / docstrings):
  F1 commands       /status /history /log /live /report /alerts /autoreport /set /help
  F2 Rich Messages  table/card reports (Bot API 10.1+), falls back to plain HTML
  F3 inline buttons callbacks edit the message in place
  F4 live mode      one message edited every few seconds
  F5 alerts         threshold + board-offline alerts, with hysteresis and cooldown
  F6 auto report    periodic summary
  F7 owner lock     the first chat to /start owns the bot
  F8 rate limits    >=1 s between sends per chat, retry on 429
  F9 long polling   getUpdates (no webhook: the host is behind NAT)

Config comes from environment variables (see .env.example); thresholds can then be changed from chat (/set).
"""
import html
import json
import math
import os
import re
import sqlite3
import sys
import threading
import time
import traceback
from contextlib import closing
from datetime import datetime, timedelta, timezone

import httpx

# ---------------------------------------------------------------- config
# Bot token from @BotFather (empty = bot disabled); other tuning knobs follow.
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
# API_BASE is overridable so tests can point at a fake server
API_BASE = os.environ.get("TELEGRAM_API_BASE", "https://api.telegram.org").rstrip("/")
DB_PATH = os.environ.get("DB_PATH", "data.db")
STATE_PATH = os.environ.get("BOT_STATE_PATH", "bot_data/state.json")

MINIAPP_URL = os.environ.get("MINIAPP_URL", "").strip()  # public https URL of /app
USE_RICH = os.environ.get("USE_RICH_MESSAGES", "1") != "0"
REPORT_INTERVAL_MIN = float(os.environ.get("REPORT_INTERVAL_MIN", "30"))
TEMP_ALERT_C = float(os.environ.get("TEMP_ALERT_C", "38"))
HUMID_ALERT_PCT = float(os.environ.get("HUMID_ALERT_PCT", "85"))
ALERT_COOLDOWN_MIN = float(os.environ.get("ALERT_COOLDOWN_MIN", "10"))
STALE_SEC = float(os.environ.get("STALE_SEC", "60"))
MONITOR_INTERVAL_SEC = float(os.environ.get("MONITOR_INTERVAL_SEC", "5"))
LIVE_INTERVAL_SEC = float(os.environ.get("LIVE_INTERVAL_SEC", "10"))
LIVE_MAX_MIN = float(os.environ.get("LIVE_MAX_MIN", "10"))
HYSTERESIS = 1.0  # an alert clears only this far below its threshold
RICH_MAX_FAILS = 3

# Thresholds that can be changed from chat (/set); chat overrides persist in the state file.
DEFAULTS = {"temp": TEMP_ALERT_C, "humid": HUMID_ALERT_PCT, "stale": STALE_SEC,
            "cooldown": ALERT_COOLDOWN_MIN, "report": REPORT_INTERVAL_MIN}
LIMITS = {"temp": (0, 100), "humid": (1, 100), "stale": (10, 3600), "cooldown": (1, 1440), "report": (0, 1440)}
SETTING_LABELS = {"temp": "อุณหภูมิ", "humid": "ความชื้น", "stale": "บอร์ดเงียบเกิน",
                  "cooldown": "เตือนซ้ำทุก", "report": "รายงานอัตโนมัติทุก"}
SETTING_UNITS = {"temp": "°C", "humid": "%", "stale": "วินาที", "cooldown": "นาที", "report": "นาที"}

# /log: default window and step; the table is capped so one message stays readable.
LOG_DEFAULT_MIN, LOG_DEFAULT_STEP_MIN = 60, 5
LOG_MAX_MIN, LOG_MAX_ROWS = 1440, 72
LOG_STEPS = (1, 2, 5, 10, 15, 20, 30, 60)

TZ = timezone(timedelta(hours=7))  # fixed UTC+7; the slim image has no tzdata

# node id -> (name, unit, emoji); keep in sync with NODE_* in the firmware Config.h
NODES = {
    1: ("BMP280 Temperature", "°C", "🌡"),
    2: ("BMP280 Pressure", "hPa", "💨"),
    3: ("HTS221 Temperature", "°C", "🌡"),
    4: ("HTS221 Humidity", "%", "💧"),
}

# Inline keyboards; 'style' colours a button (primary=blue, danger=red)
KEYBOARD = {"inline_keyboard": [
    [{"text": "📊 Status", "callback_data": "status", "style": "primary"},
     {"text": "📈 1 ชม.", "callback_data": "history", "style": "primary"}],
    [{"text": "🔴 Live", "callback_data": "live", "style": "danger"},
     {"text": "🔔 แจ้งเตือน", "callback_data": "alerts"}],
    [{"text": "📋 Log 1 ชม.", "callback_data": "log"}],
]}
STOP_KEYBOARD = {"inline_keyboard": [[{"text": "⏹ หยุด live", "callback_data": "stop", "style": "danger"}]]}

def settings_keyboard(state, s=None):
    """[F3][F5][F6] Settings buttons: switches show their state (green = on, red = off); -/+ tune thresholds."""
    s = s or DEFAULTS

    def switch(label, on, action):
        return [{"text": f"{label}: {'เปิด ✅' if on else 'ปิด ⏸'}", "callback_data": action,
                 "style": "success" if on else "danger"}]

    def stepper(emoji, name, unit, step):
        return [{"text": f"{emoji} −{step:g}", "callback_data": f"adj:{name}:-{step:g}"},
                {"text": f"{emoji} {s[name]:g} {unit}", "callback_data": "noop"},
                {"text": f"{emoji} +{step:g}", "callback_data": f"adj:{name}:{step:g}"}]

    return {"inline_keyboard": [
        switch("🔔 แจ้งเตือน", state.get("alerts_enabled"), "toggle_alerts"),
        switch("🗓 รายงานอัตโนมัติ", state.get("report_enabled"), "toggle_report"),
        stepper("🌡", "temp", "°C", 1),
        stepper("💧", "humid", "%", 5),
        [{"text": "⬅ กลับ", "callback_data": "status"}],
    ]}


# Command menu registered with setMyCommands
COMMANDS = [
    {"command": "status", "description": "ค่าเซนเซอร์ล่าสุด"},
    {"command": "history", "description": "สรุปย้อนหลัง (เช่น /history 30 = 30 นาที)"},
    {"command": "log", "description": "ตารางอุณหภูมิย้อนหลัง (เช่น /log 3h 10m)"},
    {"command": "live", "description": "ข้อความที่อัปเดตสดอัตโนมัติ"},
    {"command": "report", "description": "ส่งรายงานทันที"},
    {"command": "alerts", "description": "เปิด/ปิดแจ้งเตือนเกินเกณฑ์ (/alerts on|off)"},
    {"command": "autoreport", "description": "เปิด/ปิดรายงานอัตโนมัติ (/autoreport on|off)"},
    {"command": "set", "description": "ปรับเกณฑ์ (เช่น /set temp 40, /set reset)"},
    {"command": "app", "description": "เปิด Mini App แสดงข้อมูลเซ็นเซอร์"},
    {"command": "help", "description": "วิธีใช้"},
]

# (command, description) rows reused by the plain and Rich help text
HELP_ROWS = [
    ("/status", "ค่าล่าสุด"),
    ("/history [นาที]", "สรุปย้อนหลัง"),
    ("/log [ช่วง] [ทุก]", "ตารางอุณหภูมิย้อนหลัง"),
    ("/live", "อัปเดตสด"),
    ("/report", "รายงานทันที"),
    ("/alerts [on|off]", "แจ้งเตือนเกินเกณฑ์"),
    ("/autoreport [on|off]", "รายงานอัตโนมัติ"),
    ("/set ชื่อ ค่า", "ปรับเกณฑ์"),
    ("/app", "เปิด Mini App"),
]


def log(*parts):
    """Print a log line with the bot token redacted."""
    msg = " ".join(str(p) for p in parts)
    if TOKEN:
        msg = msg.replace(TOKEN, "***")
    print(f"[bot] {msg}", flush=True)


def utcnow():
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------- database

def ensure_table():
    """Create the readings table if it does not exist yet."""
    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS data ("
                     "_id INTEGER PRIMARY KEY AUTOINCREMENT, node INTEGER, value REAL, "
                     "ts TEXT DEFAULT (datetime('now')));")
        conn.commit()


def parse_ts(ts):
    """SQLite UTC timestamp text -> aware datetime."""
    return datetime.strptime(ts, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)


def latest():
    """[F1] Newest reading per node: {node: (value, datetime)}."""
    out = {}
    with closing(sqlite3.connect(DB_PATH)) as conn:
        for node in NODES:
            row = conn.execute(
                "SELECT value, ts FROM data WHERE node = ? ORDER BY _id DESC LIMIT 1;",
                (node,)).fetchone()
            if row:
                out[node] = (row[0], parse_ts(row[1]))
    return out


def stats(minutes):
    """[F1] min/avg/max/count per node over the last N minutes."""
    since = (utcnow() - timedelta(minutes=minutes)).strftime("%Y-%m-%d %H:%M:%S")
    with closing(sqlite3.connect(DB_PATH)) as conn:
        rows = conn.execute(
            "SELECT node, MIN(value), AVG(value), MAX(value), COUNT(*) "
            "FROM data WHERE ts >= ? GROUP BY node;", (since,)).fetchall()
    return {r[0]: r[1:] for r in rows}



def log_rows(duration_min, step_min, now):
    """[F1] Clock-aligned buckets: ([(bucket_start_epoch, temp, humid)], (min, avg, max) of temperature)."""
    step = int(step_min * 60)
    end = int(now.timestamp())
    first, last = (end - int(duration_min * 60)) // step, end // step
    since = datetime.fromtimestamp(first * step, timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    per_bucket = {}  # bucket -> {node: average}
    with closing(sqlite3.connect(DB_PATH)) as conn:
        for b, node, avg in conn.execute(
                "SELECT CAST(strftime('%s', ts) AS INTEGER) / ?, node, AVG(value) FROM data "
                "WHERE ts >= ? AND node IN (1, 3, 4) GROUP BY 1, node;", (step, since)):
            per_bucket.setdefault(b, {})[node] = avg
        summary = conn.execute("SELECT MIN(value), AVG(value), MAX(value) FROM data "
                               "WHERE ts >= ? AND node IN (1, 3);", (since,)).fetchone()
    rows = []
    for b in range(first, last + 1):
        v = per_bucket.get(b, {})
        temps = [v[n] for n in (1, 3) if n in v]  # temperature = mean of the two sensors
        rows.append((b * step, sum(temps) / len(temps) if temps else None, v.get(4)))
    return rows, summary


# ----------------------------------------- plain-text formatting (HTML parse mode)
def fmt_ago(secs):
    """Seconds -> short Thai duration text."""
    if secs < 60:
        return f"{int(secs)} วินาที"
    if secs < 3600:
        return f"{int(secs // 60)} นาที"
    return f"{secs / 3600:.1f} ชั่วโมง"


def fmt_minutes(m):
    """Minutes -> '30 นาที' / '3 ชั่วโมง'."""
    return f"{m:g} นาที" if m < 120 else f"{m / 60:g} ชั่วโมง"


def parse_duration(tok):
    """'90' / '90m' / '2h' / '1d' -> minutes (float), or None when it does not parse."""
    m = re.fullmatch(r"(\d+(?:[.,]\d+)?)\s*([mhd]?)", tok.strip().lower())
    if not m:
        return None
    return float(m.group(1).replace(",", ".")) * {"": 1, "m": 1, "h": 60, "d": 1440}[m.group(2)]


def parse_log_args(args):
    """[F1] '/log [duration] [step]' -> (duration_min, step_min, note, error). Caps the row count."""
    usage = "รูปแบบ: /log [ช่วงเวลา] [ทุกกี่นาที] เช่น /log 3h 10m (ช่วงเวลา 1 นาที – 24 ชั่วโมง)"
    if len(args) > 2:
        return None, None, None, usage
    duration = parse_duration(args[0]) if args else float(LOG_DEFAULT_MIN)
    step = parse_duration(args[1]) if len(args) == 2 else None
    if duration is None or (len(args) == 2 and step is None):
        return None, None, None, usage
    if not 1 <= duration <= LOG_MAX_MIN:
        return None, None, None, "ช่วงเวลาต้องอยู่ระหว่าง 1 นาที – 24 ชั่วโมง"
    if step is None:
        step = LOG_DEFAULT_STEP_MIN if duration >= 2 * LOG_DEFAULT_STEP_MIN else 1
    step = int(round(step))
    if not 1 <= step <= 60:
        return None, None, None, "ระยะห่างต้องอยู่ระหว่าง 1 – 60 นาที"
    if step > duration:
        return None, None, None, "ระยะห่างต้องไม่เกินช่วงเวลาทั้งหมด"
    note = None
    if math.ceil(duration / step) + 1 > LOG_MAX_ROWS:  # too many rows for one message -> widen the step
        step = next(c for c in LOG_STEPS if math.ceil(duration / c) + 1 <= LOG_MAX_ROWS)
        note = f"ปรับเป็นทุก {step} นาที เพื่อไม่ให้ตารางยาวเกิน {LOG_MAX_ROWS} แถว"
    return duration, step, note, None


def validate_setting(name, raw):
    """[F5][F6] -> (value, error) for '/set name raw'; values are range-checked and rounded."""
    try:
        v = float(str(raw).replace(",", "."))
    except ValueError:
        return None, f"'{html.escape(str(raw))}' ไม่ใช่ตัวเลข"
    if v != v or v in (float("inf"), float("-inf")):
        return None, "ค่าต้องเป็นตัวเลขปกติ"
    lo, hi = LIMITS[name]
    if not lo <= v <= hi:
        return None, f"{SETTING_LABELS[name]} ต้องอยู่ระหว่าง {lo:g} – {hi:g} {SETTING_UNITS[name]}"
    return round(v, 1), None


def set_usage(s):
    """[F5][F6] Help text for /set with the current values."""
    lines = ["ปรับเกณฑ์: /set ชื่อ ค่า   (เช่น /set temp 40)"]
    for name, (lo, hi) in LIMITS.items():
        lines.append(f"• {name} — {SETTING_LABELS[name]} ({SETTING_UNITS[name]}) {lo:g}–{hi:g} · ตอนนี้ {s[name]:g}")
    lines.append("• /set reset — คืนค่าเริ่มต้น")
    return "\n".join(lines)


def status_text(data, now, s=None):
    """[F1] Plain-text /status (also the Rich fallback)."""
    s = s or DEFAULTS
    lines = ["🌿 <b>Cucumber Environment</b>"]
    if not data:
        lines.append("ยังไม่มีข้อมูลจากบอร์ด")
        return "\n".join(lines)
    for node, (name, unit, emoji) in NODES.items():
        if node in data:
            lines.append(f"{emoji} {html.escape(name)}: <b>{data[node][0]:.2f}</b> {unit}")
        else:
            lines.append(f"{emoji} {html.escape(name)}: –")
    newest = max(ts for _, ts in data.values())
    age = (now - newest).total_seconds()
    lines.append(f"\n🕒 {newest.astimezone(TZ):%H:%M:%S} (เวลาไทย) · {fmt_ago(age)}ที่แล้ว")
    if age > s["stale"]:
        lines.append("⚠️ ข้อมูลไม่อัปเดตนานผิดปกติ — เช็คบอร์ด/WiFi/MQTT")
    return "\n".join(lines)


def history_text(minutes):
    """[F1] Plain-text /history."""
    st = stats(minutes)
    label = fmt_minutes(minutes)
    lines = [f"📈 <b>สรุป {label}ล่าสุด</b>"]
    if not st:
        lines.append("ไม่มีข้อมูลในช่วงนี้")
        return "\n".join(lines)
    for node, (name, unit, emoji) in NODES.items():
        if node in st:
            lo, avg, hi, n = st[node]
            lines.append(f"{emoji} {html.escape(name)}: min {lo:.2f} · avg {avg:.2f} · "
                         f"max {hi:.2f} {unit} <i>(n={n})</i>")
    return "\n".join(lines)


def alerts_text(state, s=None):
    """[F5][F6] Plain-text alert/auto-report settings."""
    s = s or DEFAULTS
    on = "เปิด ✅" if state.get("alerts_enabled") else "ปิด ⏸"
    auto = "เปิด ✅" if state.get("report_enabled") else "ปิด ⏸"
    every = f"ทุก {s['report']:g} นาที" if s["report"] > 0 else "ปิด"
    return (f"🔔 <b>แจ้งเตือน</b>: {on}\n"
            f"• อุณหภูมิ &gt; {s['temp']:g} °C\n"
            f"• ความชื้น &gt; {s['humid']:g} %\n"
            f"• บอร์ดเงียบเกิน {s['stale']:g} วินาที\n"
            f"• เตือนซ้ำทุก {s['cooldown']:g} นาที\n"
            f"🗓 <b>รายงานอัตโนมัติ</b>: {auto} ({every})\n\nแตะปุ่มด้านล่างเพื่อเปิด/ปิดหรือปรับเกณฑ์")


def welcome_text():
    return ("🌿 <b>Cucumber Environment Bot</b>\n"
            "ผูกแชทนี้กับบอทแล้ว — จะส่งรายงานและแจ้งเตือนมาที่นี่\n\n"
            + "\n".join(f"{html.escape(c)} — {d}" for c, d in HELP_ROWS))


def log_title(duration, step):
    return f"📋 Log อุณหภูมิ {fmt_minutes(duration)}ล่าสุด · ทุก {step} นาที"


def log_label(epoch, multi_day):
    return datetime.fromtimestamp(epoch, TZ).strftime("%d/%m %H:%M" if multi_day else "%H:%M")


def _log_has_data(rows):
    return any(t is not None or h is not None for _, t, h in rows)


def _log_multi_day(rows):
    return datetime.fromtimestamp(rows[0][0], TZ).date() != datetime.fromtimestamp(rows[-1][0], TZ).date()


def log_text(rows, summary, duration, step, note=None):
    """[F1] Plain-text /log: summary line + monospace table."""
    lines = [f"<b>{log_title(duration, step)}</b>"]
    if note:
        lines.append(f"<i>{html.escape(note)}</i>")
    if not _log_has_data(rows):
        lines.append("ไม่มีข้อมูลในช่วงนี้")
        return "\n".join(lines)
    lo, avg, hi = summary
    lines.append(f"🌡 min {lo:.1f} · avg {avg:.1f} · max {hi:.1f} °C")
    multi = _log_multi_day(rows)
    body = []
    for i, (epoch, t, h) in enumerate(rows):
        tv = "  –  " if t is None else f"{t:5.1f}"
        hv = " –" if h is None else f"{h:3.0f}"
        body.append(f"{log_label(epoch, multi)}  {tv} °C  {hv} %" + (" ← ตอนนี้" if i == len(rows) - 1 else ""))
    lines.append("<pre>" + "\n".join(body) + "</pre>")
    return "\n".join(lines)


def report_text(s=None):
    """[F6] Status + 60-minute summary (plain text)."""
    return status_text(latest(), utcnow(), s) + "\n\n" + history_text(60)


# ------------------------------------------ formatting: Rich Messages [F2]

# Note: never start a rich message with <h1>-<h6>; clients draw it flush against the bubble's top edge.
def tg_time(dt, fmt, fallback):
    """[F2] <tg-time>: viewer-local time ('T') or self-updating relative time ('r')."""
    return f'<tg-time unix="{int(dt.timestamp())}" format="{fmt}">{fallback}</tg-time>'


def rich_headline(data):
    """[F2] Card header: big temperature plus humidity/pressure."""
    temps = [data[n][0] for n in (1, 3) if n in data]
    out = ""
    if temps:
        out += f"<h1>🌡 {sum(temps) / len(temps):.1f} °C</h1>"
    extra = []
    if 4 in data:
        extra.append(f"💧 ความชื้น <b>{data[4][0]:.0f} %</b>")
    if 2 in data:
        extra.append(f"💨 ความดัน <b>{data[2][0]:.0f} hPa</b>")
    if extra:
        out += "<p>" + " &nbsp;·&nbsp; ".join(extra) + "</p>"
    return out


def rich_status(data, now, s=None):
    """[F2] Status card: headline, per-sensor table, time footer."""
    s = s or DEFAULTS
    parts = ["<p><b>🌿 Cucumber Environment</b></p>"]
    if not data:
        parts.append("<p>ยังไม่มีข้อมูลจากบอร์ด</p>")
        return "".join(parts)
    parts.append(rich_headline(data))
    rows = []
    for node, (name, unit, emoji) in NODES.items():
        val = f"<b>{data[node][0]:.2f}</b>" if node in data else "–"
        rows.append(f'<tr><td>{emoji} {html.escape(name)}</td><td align="right">{val}</td>'
                    f"<td>{unit}</td></tr>")
    parts.append("<table bordered striped><tr><th>เซนเซอร์</th><th>ค่า</th><th>หน่วย</th></tr>"
                 + "".join(rows) + "</table>")
    newest = max(ts for _, ts in data.values())
    age = (now - newest).total_seconds()
    parts.append(f"<footer>🕒 {tg_time(newest, 'T', f'{newest.astimezone(TZ):%H:%M:%S}')} · "
                 f"{tg_time(newest, 'r', f'{fmt_ago(age)}ที่แล้ว')}</footer>")
    if age > s["stale"]:
        parts.append("<p>⚠️ <b>ข้อมูลไม่อัปเดตนานผิดปกติ</b> — เช็คบอร์ด/WiFi/MQTT</p>")
    return "".join(parts)


def rich_history(minutes):
    """[F2] History table (min/avg/max/n)."""
    st = stats(minutes)
    label = fmt_minutes(minutes)
    parts = [f"<p><b>📈 สรุป {label}ล่าสุด</b></p>"]
    if not st:
        parts.append("<p>ไม่มีข้อมูลในช่วงนี้</p>")
        return "".join(parts)
    rows = []
    for node, (name, unit, emoji) in NODES.items():
        if node in st:
            lo, avg, hi, n = st[node]
            rows.append(f"<tr><td>{emoji} {html.escape(name)} ({unit})</td>"
                        f'<td align="right">{lo:.2f}</td><td align="right">{avg:.2f}</td>'
                        f'<td align="right">{hi:.2f}</td><td align="right">{n}</td></tr>')
    parts.append("<table bordered striped compact><tr><th>เซนเซอร์</th><th>min</th>"
                 "<th>avg</th><th>max</th><th>n</th></tr>" + "".join(rows) + "</table>")
    return "".join(parts)


def rich_log(rows, summary, duration, step, note=None):
    """[F2] /log as a table: time | temperature | humidity (one row per clock-aligned bucket)."""
    parts = [f"<p><b>{log_title(duration, step)}</b></p>"]
    if note:
        parts.append(f"<p><i>{html.escape(note)}</i></p>")
    if not _log_has_data(rows):
        parts.append("<p>ไม่มีข้อมูลในช่วงนี้</p>")
        return "".join(parts)
    lo, avg, hi = summary
    parts.append(f"<p>🌡 min <b>{lo:.1f}</b> · avg <b>{avg:.1f}</b> · max <b>{hi:.1f}</b> °C</p>")
    multi = _log_multi_day(rows)
    trs = []
    for i, (epoch, t, h) in enumerate(rows):
        label = log_label(epoch, multi) + (" (ตอนนี้)" if i == len(rows) - 1 else "")
        trs.append(f'<tr><td>{label}</td><td align="right">{"–" if t is None else f"{t:.1f}"}</td>'
                   f'<td align="right">{"–" if h is None else f"{h:.0f}"}</td></tr>')
    parts.append("<table bordered striped compact><tr><th>เวลา</th><th>🌡 °C</th><th>💧 %</th></tr>"
                 + "".join(trs) + "</table>")
    parts.append("<footer>เวลาไทย · ค่าเฉลี่ยของ BMP280 และ HTS221 ในแต่ละช่วง</footer>")
    return "".join(parts)


def rich_report(s=None):
    """[F6] Rich report: status card + history table."""
    return rich_status(latest(), utcnow(), s) + "<hr/>" + rich_history(60)


def rich_settings(state, s=None):
    """[F2][F5] Settings page: state table + thresholds (changed with the buttons or /set)."""
    s = s or DEFAULTS

    def word(on):
        return "✅ เปิด" if on else "⏸ ปิด"
    every = f"ทุก {s['report']:g} นาที" if s["report"] > 0 else "ปิด"
    return ("<p><b>🔔 การตั้งค่าแจ้งเตือน</b></p>"
            "<table bordered compact>"
            f"<tr><td>แจ้งเตือนเกินเกณฑ์</td><td>{word(state.get('alerts_enabled'))}</td></tr>"
            f"<tr><td>รายงานอัตโนมัติ ({every})</td><td>{word(state.get('report_enabled'))}</td></tr></table>"
            f"<ul><li>อุณหภูมิ &gt; {s['temp']:g} °C</li><li>ความชื้น &gt; {s['humid']:g} %</li>"
            f"<li>บอร์ดเงียบเกิน {s['stale']:g} วินาที</li><li>เตือนซ้ำทุก {s['cooldown']:g} นาที</li></ul>"
            "<footer>ปรับด้วยปุ่ม − / + หรือพิมพ์ /set temp 40 · /set reset คืนค่าเริ่มต้น</footer>")


def rich_welcome():
    """[F1][F2] Welcome/help: command table."""
    rows = "".join(f"<tr><td>{html.escape(c)}</td><td>{d}</td></tr>" for c, d in HELP_ROWS)
    return ("<p><b>🌿 Cucumber Environment Bot</b></p>"
            "<p>ผูกแชทนี้กับบอทแล้ว — รายงานและแจ้งเตือนจะมาที่นี่</p>"
            f"<table bordered compact>{rows}</table>"
            "<footer>แตะปุ่มด้านล่างเพื่อเริ่มได้เลย 👇</footer>")


# ------------------------------------------------------------------ state

class State:
    """[F7] Persistent bot state (owner chat, alert/report switches) in a JSON file."""

    def __init__(self, path):
        self.path = path
        self.lock = threading.Lock()
        self.data = {"owner_chat_id": None, "alerts_enabled": True, "report_enabled": True, "settings": {}}
        try:
            with open(path, encoding="utf-8") as f:
                self.data.update(json.load(f))
        except (OSError, ValueError):
            pass
        preset = os.environ.get("TELEGRAM_ALLOWED_CHAT_ID", "").strip()
        if preset:
            self.data["owner_chat_id"] = int(preset)

    def get(self, key):
        with self.lock:
            return self.data[key]

    def settings(self):
        """Effective thresholds: chat overrides on top of the env defaults."""
        with self.lock:
            over = self.data.get("settings") or {}
            return {**DEFAULTS, **{k: v for k, v in over.items() if k in DEFAULTS}}

    def set_setting(self, name, value):
        with self.lock:
            over = dict(self.data.get("settings") or {})
        over[name] = value
        self.set(settings=over)

    def reset_settings(self):
        self.set(settings={})

    def set(self, **kw):
        with self.lock:
            self.data.update(kw)
            os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
            tmp = self.path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self.data, f)
            os.replace(tmp, self.path)


# --------------------------------------------------------- telegram client

class TelegramError(Exception):
    """Bot API returned ok=false (status = HTTP code, 0 = network error)."""

    def __init__(self, status, description):
        super().__init__(f"{status}: {description}")
        self.status = status
        self.description = description


class Telegram:
    """Thin Bot API client: calls, retries, paced sends."""

    def __init__(self, token):
        self.base = f"{API_BASE}/bot{token}"
        self.http = httpx.Client(timeout=httpx.Timeout(45.0, connect=10.0))
        self._send_lock = threading.Lock()
        self._last_send = {}

    def call(self, method, **params):
        """POST any Bot API method; [F8] waits retry_after and retries on 429."""
        last_err = None
        for attempt in range(4):
            try:
                r = self.http.post(f"{self.base}/{method}", json=params)
            except httpx.HTTPError as exc:
                last_err = TelegramError(0, f"network: {type(exc).__name__}")
                time.sleep(min(2 ** attempt, 8))
                continue
            try:
                body = r.json()
            except ValueError:
                body = {"ok": False, "description": r.text[:200]}
            if body.get("ok"):
                return body["result"]
            if r.status_code == 429:  # [F8] flood control
                wait = body.get("parameters", {}).get("retry_after", 1)
                log(f"429 on {method}, waiting {wait}s")
                time.sleep(wait + 0.5)
                last_err = TelegramError(429, body.get("description", ""))
                continue
            raise TelegramError(r.status_code, body.get("description", ""))
        raise last_err or TelegramError(0, "gave up")

    def _paced(self, method, chat_id, **params):
        """[F8] Send with >=1.05 s spacing per chat."""
        with self._send_lock:
            wait = 1.05 - (time.monotonic() - self._last_send.get(chat_id, 0.0))
            if wait > 0:
                time.sleep(wait)
            try:
                return self.call(method, chat_id=chat_id, **params)
            finally:
                self._last_send[chat_id] = time.monotonic()

    def send(self, chat_id, text, **extra):
        """Send a plain HTML message."""
        return self._paced("sendMessage", chat_id, text=text[:4000], parse_mode="HTML",
                           link_preview_options={"is_disabled": True}, **extra)

    def send_rich(self, chat_id, html_body, **extra):
        """[F2] Send a Rich Message (sendRichMessage, 'html' field)."""
        return self._paced("sendRichMessage", chat_id, rich_message={"html": html_body}, **extra)

    def _edit(self, **params):
        """editMessageText; 'message is not modified' is not an error."""
        params = {k: v for k, v in params.items() if v is not None}
        try:
            return self.call("editMessageText", **params)
        except TelegramError as exc:
            if "message is not modified" in exc.description:
                return None
            raise

    def edit(self, chat_id, message_id, text, reply_markup=None):
        """[F3][F4] Edit a plain message in place."""
        return self._edit(chat_id=chat_id, message_id=message_id, text=text[:4000],
                          parse_mode="HTML", link_preview_options={"is_disabled": True},
                          reply_markup=reply_markup)

    def edit_rich(self, chat_id, message_id, html_body, reply_markup=None):
        """[F2][F3][F4] Edit a Rich Message in place."""
        return self._edit(chat_id=chat_id, message_id=message_id,
                          rich_message={"html": html_body}, reply_markup=reply_markup)


# ----------------------------------------------------------------- alerts

class Monitor:
    """[F5] Decides which alerts to send: thresholds, board offline, hysteresis, reminder cooldown."""

    def __init__(self, cfg=None):
        self.cfg = cfg or (lambda: DEFAULTS)  # returns the effective thresholds; may change between ticks
        self.active = {}
        self.last_sent = {}

    def _check(self, key, cond, clear_cond, alert, recovered, now, out, cooldown_min):
        if cond:
            if key not in self.active:
                self.active[key] = True
                self.last_sent[key] = now
                out.append(alert)
            elif (now - self.last_sent[key]).total_seconds() >= cooldown_min * 60:
                self.last_sent[key] = now
                out.append(alert + "\n<i>(ยังไม่กลับสู่ปกติ)</i>")
        elif key in self.active and clear_cond:
            del self.active[key]
            out.append(recovered)

    def tick(self, data, now):
        """One check pass over the latest data -> list of alert texts."""
        s = self.cfg()
        out = []
        if not data:
            return out
        newest = max(ts for _, ts in data.values())
        age = (now - newest).total_seconds()
        offline = age > s["stale"]
        self._check("offline", offline, not offline,
                    f"📵 <b>บอร์ดเงียบ</b> — ไม่ได้รับข้อมูลมา {fmt_ago(age)}",
                    "✅ บอร์ดกลับมาส่งข้อมูลแล้ว", now, out, s["cooldown"])
        if offline:
            return out
        temps = [data[n][0] for n in (1, 3) if n in data]
        if temps:
            t = max(temps)
            self._check("temp", t > s["temp"], t <= s["temp"] - HYSTERESIS,
                        f"🔥 <b>อุณหภูมิสูง</b> {t:.2f} °C (เกณฑ์ {s['temp']:g})",
                        f"🆗 อุณหภูมิกลับสู่ปกติ ({t:.2f} °C)", now, out, s["cooldown"])
        if 4 in data:
            h = data[4][0]
            self._check("humid", h > s["humid"], h <= s["humid"] - HYSTERESIS,
                        f"💦 <b>ความชื้นสูง</b> {h:.2f} % (เกณฑ์ {s['humid']:g})",
                        f"🆗 ความชื้นกลับสู่ปกติ ({h:.2f} %)", now, out, s["cooldown"])
        return out


# -------------------------------------------------------------------- bot

class Bot:
    """Routes Telegram updates to the features above."""

    def __init__(self, tg, state):
        self.tg = tg
        self.state = state
        self.live = {}
        self.last_deny = {}
        self.rich_fail = 0

    # ---- Sending / editing: Rich first, plain fallback [F2][F3]
    def rich_enabled(self):
        return USE_RICH and self.rich_fail < RICH_MAX_FAILS

    def _rich_failed(self, exc):
        """[F2] Count Rich rejections (400/404); stop using Rich after RICH_MAX_FAILS in a row."""
        if exc.status in (400, 404):
            self.rich_fail += 1
            log(f"Rich message ถูกปฏิเสธ ({self.rich_fail}/{RICH_MAX_FAILS}):", exc)
            if self.rich_fail >= RICH_MAX_FAILS:
                log("เลิกใช้ Rich message → ใช้ข้อความปกติแทน")

    def reply(self, chat_id, classic, rich_html, kb=None):
        """[F2] Send a new message (Rich first, plain fallback). Returns (message, used_rich)."""
        extra = {"reply_markup": kb} if kb else {}
        if self.rich_enabled():
            try:
                msg = self.tg.send_rich(chat_id, rich_html, **extra)
                self.rich_fail = 0
                return msg, True
            except TelegramError as exc:
                self._rich_failed(exc)
        return self.tg.send(chat_id, classic, **extra), False

    def update(self, chat_id, message_id, classic, rich_html, kb=None):
        """[F3] Edit the message a button was pressed on; if that fails, send a new one."""
        try:
            if self.rich_enabled():
                self.tg.edit_rich(chat_id, message_id, rich_html, kb)
            else:
                self.tg.edit(chat_id, message_id, classic, kb)
        except TelegramError as exc:
            log("แก้ข้อความไม่ได้ → ส่งใหม่แทน:", exc)
            if self.rich_enabled():
                self._rich_failed(exc)
            self.reply(chat_id, classic, rich_html, kb)

    # ---- Owner lock [F7]
    def deny(self, chat_id):
        """[F7] Tell a non-owner chat the bot is taken (at most once a minute)."""
        if time.monotonic() - self.last_deny.get(chat_id, -1e9) > 60:
            self.last_deny[chat_id] = time.monotonic()
            self.tg.send(chat_id, "⛔ บอทนี้ถูกผูกกับแชทอื่นไปแล้ว")

    # ---- Live mode [F4]
    def live_html(self):
        """[F4] Live text as (plain, rich)."""
        data, now, s = latest(), utcnow(), self.state.settings()
        tag = f"🔴 LIVE · อัปเดตทุก {LIVE_INTERVAL_SEC:g} วินาที"
        return (status_text(data, now, s) + f"\n<b>{tag}</b>",
                rich_status(data, now, s) + f"<p><b>{tag}</b></p>")

    def start_live(self, chat_id):
        """[F4] Send the first message and start a thread that keeps editing it."""
        self.stop_live(chat_id)
        stop = threading.Event()
        self.live[chat_id] = stop
        classic, rich_html = self.live_html()
        sent, used_rich = self.reply(chat_id, classic, rich_html, STOP_KEYBOARD)
        threading.Thread(target=self._live_loop, args=(chat_id, sent["message_id"], stop, used_rich),
                         daemon=True).start()

    def stop_live(self, chat_id):
        ev = self.live.get(chat_id)
        if ev:
            ev.set()

    def _live_loop(self, chat_id, message_id, stop, used_rich):
        """[F4] Edit every LIVE_INTERVAL_SEC until stopped, timed out or the message is gone."""
        def edit(classic, rich_html, kb):
            if used_rich:
                self.tg.edit_rich(chat_id, message_id, rich_html, kb)
            else:
                self.tg.edit(chat_id, message_id, classic, kb)

        deadline = time.monotonic() + LIVE_MAX_MIN * 60
        reason = "สิ้นสุด live"
        try:
            while not stop.wait(LIVE_INTERVAL_SEC):
                if time.monotonic() > deadline:
                    reason = f"สิ้นสุด live (ครบ {LIVE_MAX_MIN:g} นาที)"
                    break
                classic, rich_html = self.live_html()
                edit(classic, rich_html, STOP_KEYBOARD)
        except TelegramError as exc:
            log("live loop ended:", exc)
            return
        finally:
            if self.live.get(chat_id) is stop:
                del self.live[chat_id]
        try:
            data, now, s = latest(), utcnow(), self.state.settings()
            edit(status_text(data, now, s) + f"\n⏹ {reason}",
                 rich_status(data, now, s) + f"<p>⏹ {reason}</p>", KEYBOARD)
        except TelegramError as exc:
            log("final live edit failed:", exc)

    def set_from_args(self, key, args):
        """[F5][F6] '/alerts on|off': set the switch; any other argument (or none) changes nothing."""
        if args and args[0].lower() in ("on", "off"):
            self.state.set(**{key: args[0].lower() == "on"})

    def flip(self, key):
        """[F3][F5][F6] Settings button: flip the switch."""
        self.state.set(**{key: not self.state.get(key)})

    def show_settings(self, chat_id, message_id=None):
        """[F5][F6] Settings page; edits the pressed message in place when message_id is given."""
        s = self.state.settings()
        kb = settings_keyboard(self.state, s)
        classic, rich_html = alerts_text(self.state, s), rich_settings(self.state.data, s)
        if message_id is None:
            self.reply(chat_id, classic, rich_html, kb)
        else:
            self.update(chat_id, message_id, classic, rich_html, kb)

    def on_set(self, chat_id, args):
        """[F5][F6] '/set name value' changes a threshold; '/set reset' restores the defaults."""
        if args and args[0].lower() == "reset":
            self.state.reset_settings()
            return self.show_settings(chat_id)
        if len(args) != 2 or args[0].lower() not in DEFAULTS:
            return self.tg.send(chat_id, set_usage(self.state.settings()))
        name = args[0].lower()
        value, err = validate_setting(name, args[1])
        if err:
            return self.tg.send(chat_id, f"⚠️ {err}")
        self.state.set_setting(name, value)
        self.show_settings(chat_id)

    def adjust(self, name, delta):
        """[F3][F5] Settings -/+ button: move a threshold by delta, clamped to its limits."""
        if name not in DEFAULTS:
            return
        lo, hi = LIMITS[name]
        cur = self.state.settings()[name]
        new = round(min(max(cur + delta, lo), hi), 1)
        if new != cur:
            self.state.set_setting(name, new)

    def send_log(self, chat_id, args, message_id=None):
        """[F1][F2] /log: temperature/humidity table; edits the pressed message when message_id is given."""
        duration, step, note, err = parse_log_args(args)
        if err:
            return self.tg.send(chat_id, err)
        rows, summary = log_rows(duration, step, utcnow())
        classic, rich_html = log_text(rows, summary, duration, step, note), rich_log(rows, summary, duration, step, note)
        if message_id is None:
            self.reply(chat_id, classic, rich_html, KEYBOARD)
        else:
            self.update(chat_id, message_id, classic, rich_html, KEYBOARD)

    # ---- Update dispatch [F1][F3]
    def handle(self, update):
        if "message" in update:
            self.on_message(update["message"])
        elif "callback_query" in update:
            self.on_callback(update["callback_query"])

    def on_message(self, msg):
        """[F1] Handle typed commands."""
        text = (msg.get("text") or "").strip()
        if not text.startswith("/") or msg.get("from", {}).get("is_bot"):
            return
        chat_id = msg["chat"]["id"]
        parts = text.split()
        cmd, args = parts[0].split("@")[0].lower(), parts[1:]  # '/status@mybot' -> '/status'
        owner = self.state.get("owner_chat_id")
        if cmd == "/start":
            if owner is None:
                self.state.set(owner_chat_id=chat_id)
                owner = chat_id
                log(f"owner bound to chat {chat_id}")
            if owner != chat_id:
                return self.deny(chat_id)
            return self.reply(chat_id, welcome_text(), rich_welcome(), KEYBOARD)
        if owner is None:
            return self.tg.send(chat_id, "พิมพ์ /start ก่อน เพื่อผูกบอทกับแชทนี้")
        if owner != chat_id:
            return self.deny(chat_id)

        if cmd == "/app":
            if not MINIAPP_URL.startswith("https://"):
                self.tg.send(chat_id, "ยังไม่ได้ตั้งค่า MINIAPP_URL (ต้องเป็น https://...) ใน .env")
            else:
                kb = {"inline_keyboard": [[{"text": "📊 เปิด Mini App", "web_app": {"url": MINIAPP_URL + "/app"}}]]}
                self.tg.send(chat_id, "แตะปุ่มเพื่อเปิดหน้าแสดงข้อมูลเซ็นเซอร์", reply_markup=kb)
        elif cmd == "/help":
            self.reply(chat_id, welcome_text(), rich_welcome(), KEYBOARD)
        elif cmd == "/status":
            data, now, s = latest(), utcnow(), self.state.settings()
            self.reply(chat_id, status_text(data, now, s), rich_status(data, now, s), KEYBOARD)
        elif cmd == "/history":
            try:
                minutes = min(max(float(args[0]), 1), 1440) if args else 60
            except ValueError:
                minutes = 60
            self.reply(chat_id, history_text(minutes), rich_history(minutes), KEYBOARD)
        elif cmd == "/log":
            self.send_log(chat_id, args)
        elif cmd == "/live":  # [F4]
            self.start_live(chat_id)
        elif cmd == "/report":
            s = self.state.settings()
            self.reply(chat_id, report_text(s), rich_report(s), KEYBOARD)
        elif cmd == "/alerts":
            self.set_from_args("alerts_enabled", args)
            self.show_settings(chat_id)
        elif cmd == "/autoreport":
            self.set_from_args("report_enabled", args)
            self.show_settings(chat_id)
        elif cmd == "/set":
            self.on_set(chat_id, args)
        else:
            self.tg.send(chat_id, "ไม่รู้จักคำสั่งนี้ ลอง /help")

    def on_callback(self, cb):
        """[F3] Handle inline button presses."""
        try:
            self.tg.call("answerCallbackQuery", callback_query_id=cb["id"])
        except TelegramError as exc:
            log("answerCallbackQuery:", exc)
        message = cb.get("message") or {}
        chat_id = message.get("chat", {}).get("id")
        message_id = message.get("message_id")
        if chat_id is None or message_id is None:
            return
        if self.state.get("owner_chat_id") != chat_id:
            return
        action = cb.get("data")
        if action == "status":
            data, now, s = latest(), utcnow(), self.state.settings()
            self.update(chat_id, message_id, status_text(data, now, s), rich_status(data, now, s), KEYBOARD)
        elif action == "history":
            self.update(chat_id, message_id, history_text(60), rich_history(60), KEYBOARD)
        elif action == "log":
            self.send_log(chat_id, [], message_id)
        elif action == "live":  # [F4]
            self.start_live(chat_id)
        elif action == "stop":  # [F4]
            self.stop_live(chat_id)
        elif action == "alerts":
            self.show_settings(chat_id, message_id)
        elif action == "toggle_alerts":
            self.flip("alerts_enabled")
            self.show_settings(chat_id, message_id)
        elif action == "toggle_report":
            self.flip("report_enabled")
            self.show_settings(chat_id, message_id)
        elif action and action.startswith("adj:"):
            try:
                _, name, delta = action.split(":")
                self.adjust(name, float(delta))
            except ValueError:
                log("bad adjust callback:", action)
            self.show_settings(chat_id, message_id)

    # ---- Background alerts + auto report [F5][F6]
    def monitor_loop(self):
        """[F5][F6] Background loop: send alerts and the periodic report."""
        mon = Monitor(self.state.settings)  # thresholds are re-read on every tick, so /set takes effect at once
        last_report = utcnow()
        while True:
            time.sleep(MONITOR_INTERVAL_SEC)
            try:
                owner = self.state.get("owner_chat_id")
                if owner is None:
                    continue
                now = utcnow()
                if self.state.get("alerts_enabled"):  # [F5]
                    for text in mon.tick(latest(), now):
                        self.tg.send(owner, text)
                s = self.state.settings()
                if (s["report"] > 0 and self.state.get("report_enabled")  # [F6]
                        and (now - last_report).total_seconds() >= s["report"] * 60):
                    last_report = now
                    self.reply(owner, "🗓 <b>รายงานอัตโนมัติ</b>\n\n" + report_text(s),
                               "<p><b>🗓 รายงานอัตโนมัติ</b></p>" + rich_report(s), KEYBOARD)
            except Exception:
                log("monitor error:", traceback.format_exc())

    # ---- Long-polling loop [F9]
    def poll_forever(self):
        """[F9] getUpdates long polling (works behind NAT, unlike a webhook)."""
        offset = None
        while True:
            try:
                updates = self.tg.call("getUpdates", offset=offset, timeout=30,
                                       allowed_updates=["message", "callback_query"])
            except TelegramError as exc:
                if exc.status == 409:
                    log("409 conflict: another getUpdates/webhook is active for this token")
                    time.sleep(10)
                else:
                    log("getUpdates failed:", exc)
                    time.sleep(3)
                continue
            for update in updates:
                offset = update["update_id"] + 1
                try:
                    self.handle(update)
                except Exception:
                    log("handler error:", traceback.format_exc())


def main():
    """Validate the token, clear any webhook, register commands, then run monitor + polling."""
    if not TOKEN:
        log("TELEGRAM_BOT_TOKEN ไม่ได้ตั้งค่า → ปิดบอท Telegram (ตัวอื่นทำงานต่อปกติ)")
        return 0
    ensure_table()
    tg = Telegram(TOKEN)
    try:
        me = tg.call("getMe")
    except TelegramError as exc:
        if exc.status in (401, 404):
            log("token ไม่ถูกต้อง (ตรวจ TELEGRAM_BOT_TOKEN ใน .env) → ปิดบอท")
            return 0
        raise
    log(f"พร้อมทำงาน: @{me.get('username')} (rich={'on' if USE_RICH else 'off'})")
    tg.call("deleteWebhook")  # getUpdates fails while a webhook is set
    tg.call("setMyCommands", commands=COMMANDS)
    if MINIAPP_URL.startswith("https://"):  # the chat's menu button opens the Mini App
        tg.call("setChatMenuButton", menu_button={
            "type": "web_app", "text": "Sensors", "web_app": {"url": MINIAPP_URL + "/app"}})
        log(f"Mini App: {MINIAPP_URL}/app")

    bot = Bot(tg, State(STATE_PATH))
    threading.Thread(target=bot.monitor_loop, daemon=True).start()  # [F5][F6]
    bot.poll_forever()  # [F9]
    return 0


if __name__ == "__main__":
    sys.exit(main())
