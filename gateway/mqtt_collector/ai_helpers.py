"""AI helpers for the classroom gateway.

Two small pieces of "AI", both explainable to high-school students:

1. detect_anomalies()  - statistics (z-score): is the latest reading far away from what is normal?
2. answer_question()   - ask an LLM (Ollama, e.g. running on Colab) about the sensor data.
                         If no LLM is reachable it falls back to simple rules, so the
                         classroom demo never breaks.
"""
import os
import statistics

import httpx

# Node ids (must match devices/cucumber/include/Config.h)
NODE_NAMES = {1: "อุณหภูมิ BMP280", 2: "ความดันอากาศ", 3: "อุณหภูมิ HTS221", 4: "ความชื้น"}
UNITS = {1: "°C", 2: "hPa", 3: "°C", 4: "%"}
# Smallest "normal wobble" we assume, so a very quiet sensor does not trigger false alarms.
MIN_STD = {3: 0.2, 4: 0.5}

OLLAMA_URL = os.environ.get("OLLAMA_URL", "").strip().rstrip("/")  # e.g. https://xxxx.trycloudflare.com
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:3b").strip()


def detect_anomalies(series, z_limit=3.0, min_points=20):
    """series: {node: [[ts, value], ...]} oldest first.

    Compare the average of the most recent points with the earlier points (the "baseline").
    z = (recent_mean - baseline_mean) / baseline_std.  |z| > z_limit  ->  unusual.
    Returns a list of dicts, one per node that has enough data.
    """
    results = []
    for node, points in series.items():
        node = int(node)
        values = [p[1] for p in points]
        if len(values) < min_points:
            results.append({"node": node, "name": NODE_NAMES.get(node, str(node)), "status": "not_enough_data",
                            "points": len(values)})
            continue
        split = max(min_points // 2, int(len(values) * 0.8))
        baseline, recent = values[:split], values[split:]
        mean_b = statistics.fmean(baseline)
        std_b = max(statistics.pstdev(baseline), MIN_STD.get(node, 0.2))
        z = (statistics.fmean(recent) - mean_b) / std_b
        results.append({
            "node": node,
            "name": NODE_NAMES.get(node, str(node)),
            "status": "anomaly" if abs(z) > z_limit else "normal",
            "z": round(z, 2),
            "direction": "up" if z > 0 else "down",
            "baseline_mean": round(mean_b, 2),
            "recent_mean": round(statistics.fmean(recent), 2),
            "points": len(values),
        })
    return results


def comfort_level(temp_c, humidity):
    """Very simple 'is it comfortable?' rule used by the fallback answer."""
    if temp_c is None:
        return "ยังไม่มีข้อมูลอุณหภูมิ"
    if temp_c >= 35:
        return "ร้อนมาก ควรหลีกเลี่ยงกิจกรรมกลางแจ้ง ดื่มน้ำบ่อยๆ"
    if temp_c >= 31:
        return "ร้อน" + (" และชื้น อึดอัดกว่าปกติ" if humidity and humidity >= 70 else "")
    if temp_c >= 24:
        return "อุณหภูมิกำลังสบาย"
    return "ค่อนข้างเย็น"


def _context_text(latest, anomalies):
    lines = []
    for node in (1, 2, 3, 4):
        item = latest.get(node) or latest.get(str(node))
        if item:
            lines.append(f"- {NODE_NAMES[node]}: {item['value']:.2f} {UNITS[node]} (เวลา {item['ts']} UTC)")
    flagged = [a for a in anomalies if a.get("status") == "anomaly"]
    if flagged:
        lines.append("- ความผิดปกติที่ตรวจพบ: " + "; ".join(
            f"{a['name']} {'สูงขึ้น' if a['direction'] == 'up' else 'ต่ำลง'} (z={a['z']})" for a in flagged))
    else:
        lines.append("- ยังไม่พบความผิดปกติ")
    return "\n".join(lines)


def rule_answer(question, latest, anomalies):
    """Fallback answer: keyword rules. Always works, no network needed."""
    def val(node):
        item = latest.get(node) or latest.get(str(node))
        return item["value"] if item else None

    temp, hum, pres = val(3), val(4), val(2)
    q = question.lower()
    if temp is None and hum is None:
        return "ตอนนี้ยังไม่ได้รับข้อมูลจากบอร์ด ลองเช็กว่าบอร์ดเปิดอยู่และต่อ WiFi แล้ว"
    flagged = [a for a in anomalies if a.get("status") == "anomaly"]
    if any(k in q for k in ("ผิดปกติ", "ผิดสังเกต", "แปลก", "anomaly")):
        if flagged:
            return "พบความผิดปกติ: " + "; ".join(
                f"{a['name']} {'สูงขึ้น' if a['direction'] == 'up' else 'ต่ำลง'}กว่าปกติ (z={a['z']})" for a in flagged)
        return "ตอนนี้ค่าจากเซนเซอร์ยังอยู่ในช่วงปกติ"
    if any(k in q for k in ("ความชื้น", "ชื้น", "แห้ง")) and hum is not None:
        return f"ความชื้นตอนนี้ {hum:.0f}%" + (" ค่อนข้างชื้น" if hum >= 70 else " ปกติ" if hum >= 40 else " ค่อนข้างแห้ง")
    if any(k in q for k in ("ความดัน", "ฝน", "ลม", "hpa")) and pres is not None:
        return (f"ความดันอากาศ {pres:.1f} hPa" +
                (" (ต่ำ อาจมีฝน)" if pres < 1005 else " (ปกติ)" if pres < 1020 else " (สูง ท้องฟ้าโปร่ง)"))
    if temp is not None:
        text = f"ตอนนี้อุณหภูมิ {temp:.1f} °C" + (f" ความชื้น {hum:.0f}%" if hum is not None else "")
        return text + " — " + comfort_level(temp, hum)
    return "ลองถามเรื่องอุณหภูมิ ความชื้น ความดัน หรือความผิดปกติดูนะ"


def llm_answer(question, latest, anomalies, timeout=30.0):
    """Ask Ollama (e.g. on Colab). Returns text, or None when no LLM is configured / reachable."""
    if not OLLAMA_URL:
        return None
    system = ("คุณคือผู้ช่วยสอนวิทยาศาสตร์สำหรับนักเรียน ม.ปลาย ตอบเป็นภาษาไทย สั้น กระชับ เข้าใจง่าย "
              "ใช้เฉพาะข้อมูลเซนเซอร์ที่ให้มาเท่านั้น ถ้าข้อมูลไม่พอให้บอกตามตรง ห้ามเดาตัวเลข")
    user = f"ข้อมูลเซนเซอร์ล่าสุด:\n{_context_text(latest, anomalies)}\n\nคำถาม: {question}"
    try:
        r = httpx.post(f"{OLLAMA_URL}/api/chat", timeout=timeout, json={
            "model": OLLAMA_MODEL, "stream": False,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]})
        r.raise_for_status()
        return r.json()["message"]["content"].strip()
    except (httpx.HTTPError, KeyError, ValueError):
        return None


def answer_question(question, latest, anomalies):
    """Returns {"answer": str, "source": "llm" | "rules"}."""
    text = llm_answer(question, latest, anomalies)
    if text:
        return {"answer": text, "source": "llm"}
    return {"answer": rule_answer(question, latest, anomalies), "source": "rules"}
