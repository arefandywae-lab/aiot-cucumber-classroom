import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "gateway", "mqtt_collector"))
import ai_helpers as ai  # noqa: E402


def make(values):
    return [[f"2026-01-01 00:{i:02d}:00", v] for i, v in enumerate(values)]


def test_normal_data_is_not_flagged():
    vals = [30.0 + (0.1 if i % 2 else -0.1) for i in range(40)]
    res = ai.detect_anomalies({3: make(vals)})[0]
    assert res["status"] == "normal"


def test_sudden_rise_is_flagged():
    vals = [30.0 + (0.1 if i % 2 else -0.1) for i in range(32)] + [36.0] * 8
    res = ai.detect_anomalies({3: make(vals)})[0]
    assert res["status"] == "anomaly" and res["direction"] == "up"


def test_not_enough_data():
    assert ai.detect_anomalies({4: make([60.0] * 5)})[0]["status"] == "not_enough_data"


def test_rule_answer_uses_latest_values():
    latest = {3: {"value": 33.0, "ts": "t"}, 4: {"value": 75.0, "ts": "t"}, 2: {"value": 1010.0, "ts": "t"}}
    assert "33.0" in ai.rule_answer("ตอนนี้ร้อนไหม", latest, [])
    assert "75" in ai.rule_answer("ความชื้นเท่าไหร่", latest, [])


def test_rule_answer_no_data():
    assert "ยังไม่ได้รับข้อมูล" in ai.rule_answer("ร้อนไหม", {}, [])


def test_answer_falls_back_to_rules_without_llm(monkeypatch):
    monkeypatch.setattr(ai, "OLLAMA_URL", "")
    out = ai.answer_question("ร้อนไหม", {3: {"value": 29.0, "ts": "t"}}, [])
    assert out["source"] == "rules"
