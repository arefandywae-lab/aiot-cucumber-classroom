"""Generate the Colab notebooks in ai/colab/.   python3 tools/make_notebooks.py

Kept as a script so the cells stay readable and diff-able (raw .ipynb JSON is not).
"""
import json
import pathlib

OUT = pathlib.Path(__file__).resolve().parent.parent / "ai" / "colab"
REPO = "arefandywae-lab/aiot-cucumber-classroom"


def md(text):
    return {"cell_type": "markdown", "metadata": {}, "source": text.strip("\n").splitlines(True)}


def code(text, title=None):
    meta = {"cellView": "form"} if "#@param" in text else {}
    if title:
        meta["title"] = title
    return {"cell_type": "code", "metadata": meta, "execution_count": None, "outputs": [],
            "source": text.strip("\n").splitlines(True)}


def save(name, cells, gpu):
    nb = {"cells": cells, "nbformat": 4, "nbformat_minor": 0,
          "metadata": {"colab": {"provenance": [], "name": name},
                       "kernelspec": {"name": "python3", "display_name": "Python 3"},
                       **({"accelerator": "GPU"} if gpu else {})}}
    (OUT / name).write_text(json.dumps(nb, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("wrote", name, len(cells), "cells")


# ------------------------------------------------------------------------------------ 1) LLM server
llm = [
    md(f"""
# 🤖 AI แชทสำหรับ AIoT Cucumber Classroom (บทที่ 6)

โน้ตบุ๊กนี้เปิด **LLM ขนาดเล็ก (Ollama)** บน Colab แล้วสร้างลิงก์ให้ gateway ของคุณเรียกใช้ ไม่ต้องมีการ์ดจอเอง ไม่ต้องสมัครอะไรเพิ่ม

### ทำตามนี้ (ประมาณ 5–8 นาที ครั้งแรก)
1. เมนู **Runtime → Change runtime type → T4 GPU** (ไม่เลือกก็ได้ แต่ช้ามาก)
2. กด **Runtime → Run all** หรือกดเล่นทีละเซลล์จากบนลงล่าง
3. เซลล์ที่ 5 จะพิมพ์บรรทัด `OLLAMA_URL=...` ให้ **คัดลอกไปใส่ `gateway/.env`** แล้วสั่ง `docker compose up -d mqtt_collector`
4. **อย่าปิดแท็บ** และปล่อยเซลล์ที่ 5 รันค้างไว้ตลอดการใช้งาน

> ลองเล่น: เซลล์ที่ 4 ให้เปลี่ยนคำถาม ค่าเซนเซอร์ และ system prompt ได้ ดูว่าคำตอบเปลี่ยนอย่างไร

> ขั้นตอนทั้งหมดมีที่ [หน้าเว็บบทที่ 6](https://{REPO.split('/')[0]}.github.io/{REPO.split('/')[1]}/lessons/6-ai-chat.html)
"""),
    code("""
# 1) ตรวจว่าได้ GPU ไหม แล้วติดตั้ง Ollama
import subprocess, shutil
gpu = subprocess.run(["nvidia-smi", "-L"], capture_output=True, text=True).stdout.strip()
print(gpu or "⚠ ไม่เจอ GPU! เมนู Runtime → Change runtime type → T4 GPU → Save แล้วรันเซลล์นี้ใหม่\\n"
             "   (ถ้ารันต่อบน CPU โมเดล 3b จะช้ามาก ให้เลือกโมเดล qwen2.5:1.5b ในเซลล์ถัดไป)")
!apt-get -qq install -y zstd > /dev/null
!curl -fsSL https://ollama.com/install.sh | sh > /dev/null 2>&1
print("ollama:", shutil.which("ollama") or "ติดตั้งไม่สำเร็จ")
""", "install"),
    code("""
# 2) เปิดเซิร์ฟเวอร์ Ollama และดาวน์โหลดโมเดล (ครั้งแรกใช้เวลาสักครู่)
MODEL = "qwen2.5:3b"  #@param ["qwen2.5:3b", "qwen2.5:1.5b", "gemma2:2b", "llama3.2:3b"]
import os, subprocess, time, urllib.request, json
os.environ["OLLAMA_KEEP_ALIVE"] = "2h"          # ไม่ให้โมเดลถูกถอนออกจากหน่วยความจำ
server = subprocess.Popen(["ollama", "serve"], stdout=open("/tmp/ollama.log", "w"), stderr=subprocess.STDOUT)
for _ in range(30):
    try:
        urllib.request.urlopen("http://localhost:11434/api/tags"); break
    except OSError:
        time.sleep(1)
else:
    raise RuntimeError("ollama serve ไม่ตอบ ดู log:\\n" + open("/tmp/ollama.log").read()[-1500:])
!ollama pull {MODEL}

# อุ่นเครื่อง: ครั้งแรกต้องโหลดโมเดลเข้า GPU ซึ่งช้ากว่าการตอบจริงมาก (ตั้ง timeout นานไว้)
print("กำลังโหลดโมเดลเข้าหน่วยความจำ... (CPU อาจนาน 3-5 นาที, GPU ไม่เกิน 1 นาที)")
t0 = time.time()
warm = urllib.request.Request("http://localhost:11434/api/generate",
        json.dumps({"model": MODEL, "prompt": "สวัสดี", "stream": False, "keep_alive": "2h",
                    "options": {"num_predict": 5}}).encode(), {"Content-Type": "application/json"})
try:
    urllib.request.urlopen(warm, timeout=600).read()
    print(f"โหลดเสร็จใน {time.time() - t0:.0f} วินาที")
except Exception as e:
    print("⚠ โหลดไม่สำเร็จ:", repr(e), "\\nlog ล่าสุด:\\n" + open("/tmp/ollama.log").read()[-1500:])
!ollama ps
print("ดูคอลัมน์ PROCESSOR: ต้องเป็น 100% GPU ถ้าเป็น CPU แปลว่ายังไม่ได้เลือก T4")
""", "model"),
    code("""
# 3) ทดสอบว่าโมเดลตอบได้ (ใช้ prompt แบบเดียวกับที่ gateway ส่ง)
import json, urllib.request

def ask_llm(question, context, system, model=MODEL, timeout=300):
    payload = {"model": model, "stream": False, "messages": [
        {"role": "system", "content": system},
        {"role": "user", "content": f"ข้อมูลเซนเซอร์ล่าสุด:\\n{context}\\n\\nคำถาม: {question}"}]}
    req = urllib.request.Request("http://localhost:11434/api/chat", json.dumps(payload).encode(),
                                 {"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=timeout))["message"]["content"].strip()

SYSTEM = ("คุณคือผู้ช่วยสอนวิทยาศาสตร์สำหรับนักเรียน ม.ปลาย ตอบเป็นภาษาไทย สั้น กระชับ เข้าใจง่าย "
          "ใช้เฉพาะข้อมูลเซนเซอร์ที่ให้มาเท่านั้น ถ้าข้อมูลไม่พอให้บอกตามตรง ห้ามเดาตัวเลข")
print(ask_llm("ตอนนี้ร้อนไหม", "- อุณหภูมิ HTS221: 33.1 °C\\n- ความชื้น: 62 %", SYSTEM))
""", "test"),
    md("""
## 🧪 ลองเล่น: เปลี่ยนแล้วดูว่าคำตอบเปลี่ยนไหม
ลองถาม **คำถามที่ข้อมูลตอบไม่ได้** (เช่น "พรุ่งนี้ฝนตกไหม") แล้วดูว่าโมเดล *ยอมรับว่าไม่รู้* หรือ *เดามั่ว*
จากนั้นแก้ `system prompt` ให้เข้มขึ้นหรือหลวมลง แล้วเทียบกัน
"""),
    code("""
#@title ลองเล่น: คำถาม ค่าเซนเซอร์ และ system prompt
QUESTION = "พรุ่งนี้ฝนตกไหม"  #@param {type:"string"}
TEMPERATURE = 33.1  #@param {type:"number"}
HUMIDITY = 62  #@param {type:"slider", min:10, max:100, step:1}
PRESSURE = 1004  #@param {type:"number"}
ANOMALY = False  #@param {type:"boolean"}
USE_MY_SYSTEM_PROMPT = False  #@param {type:"boolean"}
MY_SYSTEM_PROMPT = "ตอบสั้นๆ เป็นภาษาไทย ถ้าข้อมูลไม่พอให้บอกว่า ไม่ทราบ"  #@param {type:"string"}

context = (f"- อุณหภูมิ HTS221: {TEMPERATURE} °C\\n- ความชื้น: {HUMIDITY} %\\n- ความดันอากาศ: {PRESSURE} hPa\\n"
           + ("- ความผิดปกติที่ตรวจพบ: อุณหภูมิสูงขึ้น (z=5.2)" if ANOMALY else "- ยังไม่พบความผิดปกติ"))
print("คำตอบ:", ask_llm(QUESTION, context, MY_SYSTEM_PROMPT if USE_MY_SYSTEM_PROMPT else SYSTEM))
""", "playground"),
    code("""
# 5) สร้างลิงก์สาธารณะด้วย cloudflared (ไม่ต้องสมัครบัญชี) แล้วรันค้างไว้
!wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -O cloudflared
!chmod +x cloudflared
import re, subprocess, threading
tunnel = subprocess.Popen(["./cloudflared", "tunnel", "--url", "http://localhost:11434",
                           "--http-host-header", "localhost:11434"],
                          stderr=subprocess.PIPE, text=True)
found = threading.Event()
def watch():                       # อ่าน log ต่อเนื่อง ไม่งั้น pipe เต็มแล้ว tunnel ค้าง
    for line in tunnel.stderr:
        m = re.search(r"https://[-a-z0-9]+\\.trycloudflare\\.com", line)
        if m and not found.is_set():
            url = m.group(0); found.set()
            print("\\n✅ พร้อมแล้ว คัดลอกสองบรรทัดนี้ไปใส่ gateway/.env\\n")
            print(f"OLLAMA_URL={url}\\nOLLAMA_MODEL={MODEL}\\n")
            print("แล้วสั่ง:  docker compose up -d mqtt_collector")
            print(f"ทดสอบจากเครื่องคุณ:  curl {url}/api/tags")
threading.Thread(target=watch, daemon=True).start()
found.wait(60) or print("⚠ ยังไม่ได้ลิงก์ ลองหยุดเซลล์นี้แล้วรันใหม่")
import time
while True:                        # ปล่อยเซลล์นี้ให้รันค้างไว้
    time.sleep(60)
""", "tunnel"),
    md("""
### หมายเหตุ
- ลิงก์เปลี่ยนทุกครั้งที่รันใหม่ และ Colab ฟรีจะหยุดเองเมื่อไม่มีการใช้งานหรือเกินเวลา (ประมาณ 90 นาที ถึง 12 ชั่วโมง)
- ถ้า gateway ติดต่อ LLM ไม่ได้ ระบบจะตอบด้วยกฎง่ายๆ แทนโดยอัตโนมัติ (ไม่พัง)
- **ใครมีลิงก์ก็ใช้โมเดลของคุณได้** อย่าแชร์ต่อ และข้อความที่ถามจะผ่านเซิร์ฟเวอร์ของ Google/Cloudflare อย่าพิมพ์ข้อมูลส่วนตัว
- ข้อความ `Address already in use`: เซลล์ 2 รันซ้ำ ให้ Runtime → Restart session แล้วรันใหม่ตั้งแต่ต้น
"""),
]
save("cucumber_llm.ipynb", llm, gpu=True)

# ------------------------------------------------------------------------------------ 2) anomaly playground (CPU)
anom = [
    md(f"""
# 📈 สนามเล่น: AI ตรวจความผิดปกติ (บทที่ 5)

ไม่ต้องมีบอร์ด ไม่ต้องมี GPU ไม่ต้องติดตั้งอะไร กด **Runtime → Run all** ได้เลย
โค้ดในเซลล์ `detect_anomalies` **เป็นอันเดียวกับ** `gateway/mqtt_collector/ai_helpers.py` ที่ใช้จริง

สิ่งที่จะได้ลอง
1. สร้างข้อมูลเซนเซอร์จำลอง แล้วดู z-score
2. ปรับ **ความแกว่ง / ขนาดการกระโดด / เกณฑ์ z_limit** แล้วหาจุดที่ AI เริ่มเตือน
3. เห็นกับตาว่า **เตือนผิด (false alarm)** กับ **ตรวจไม่เจอ (miss)** เกิดเมื่อไหร่
4. ใส่ข้อมูลจริงจากบอร์ด (CSV) ของตัวเอง
"""),
    code("""
import statistics, random
import matplotlib.pyplot as plt

MIN_STD = {1: 0.2, 2: 0.2, 3: 0.2, 4: 0.5}

def detect_anomalies(series, z_limit=3.0, min_points=20):
    \"\"\"เหมือนใน ai_helpers.py: series = {node: [[ts, value], ...]}\"\"\"
    results = []
    for node, points in series.items():
        values = [p[1] for p in points]
        if len(values) < min_points:
            results.append({"node": node, "status": "not_enough_data", "points": len(values)}); continue
        split = max(min_points // 2, int(len(values) * 0.8))
        baseline, recent = values[:split], values[split:]
        mean_b = statistics.fmean(baseline)
        std_b = max(statistics.pstdev(baseline), MIN_STD.get(node, 0.2))
        z = (statistics.fmean(recent) - mean_b) / std_b
        results.append({"node": node, "status": "anomaly" if abs(z) > z_limit else "normal",
                        "z": round(z, 2), "baseline_mean": round(mean_b, 2),
                        "recent_mean": round(statistics.fmean(recent), 2), "std": round(std_b, 3)})
    return results
print("พร้อมแล้ว")
""", "detector"),
    code("""
#@title ลองเล่น: สร้างข้อมูลจำลองแล้วดูว่า AI เตือนไหม
NOISE = 0.2  #@param {type:"slider", min:0, max:1, step:0.05}
JUMP = 1.5  #@param {type:"slider", min:-5, max:5, step:0.1}
EVENT = "jump"  #@param ["jump", "drift", "none"]
Z_LIMIT = 3.0  #@param {type:"slider", min:0.2, max:6, step:0.1}
SEED = 7  #@param {type:"integer"}

random.seed(SEED)
N = 60
vals = []
for i in range(N):
    shift = JUMP if (EVENT == "jump" and i >= int(N * 0.8)) else JUMP * i / (N - 1) if EVENT == "drift" else 0
    vals.append(30 + shift + random.gauss(0, NOISE))
res = detect_anomalies({3: [[i, v] for i, v in enumerate(vals)]}, Z_LIMIT)[0]
print(res)

split = int(N * 0.8)
plt.figure(figsize=(9, 3.5))
plt.axhspan(res["baseline_mean"] - Z_LIMIT * res["std"], res["baseline_mean"] + Z_LIMIT * res["std"], alpha=.15, color="g", label="ช่วงปกติ")
plt.plot(vals, ".-", color="k", lw=.6)
plt.plot(range(split, N), vals[split:], "o", color="tab:orange" if res["status"] == "anomaly" else "g")
plt.axvline(split - .5, color="gray", ls=":")
plt.title(("⚠ ANOMALY" if res["status"] == "anomaly" else "normal") + f"   z = {res['z']}")
plt.xlabel("ลำดับการอ่านค่า"); plt.ylabel("°C"); plt.legend(); plt.show()
""", "playground"),
    md("""
## 🧪 โจทย์ให้ลอง (เปลี่ยนค่าในเซลล์ด้านบนแล้วกด ▶ ใหม่)
1. ตั้ง `EVENT = "none"` แล้วลด `Z_LIMIT` เหลือ 0.5 แล้วเปลี่ยน `SEED` หลายๆ ค่า (ลองประมาณ 20 ค่า) เกิด **เตือนผิด** บ่อยแค่ไหน
2. ตั้ง `EVENT = "jump"`, `JUMP = 0.5`, `Z_LIMIT = 3` AI เตือนไหม ต้อง `JUMP` เท่าไหร่ถึงเตือน
3. ตั้ง `EVENT = "drift"`, `JUMP = 4` อุณหภูมิเพิ่มถึง 4 °C แต่ AI เตือนไหม **ทำไมจึงไม่เตือน** (คิดดูว่าช่วงอ้างอิงเป็นอะไร)
4. เพิ่ม `NOISE` เป็น 0.8 แล้วหา `JUMP` ที่ทำให้เตือน สัญญาณรบกวนทำให้จับความผิดปกติยากขึ้นอย่างไร
"""),
    md("""
## ใช้ข้อมูลจริงจากบอร์ดของคุณ
ที่เครื่องที่รัน gateway ดึงข้อมูลเป็นไฟล์ แล้วอัปโหลดมาที่ Colab (ไอคอนโฟลเดอร์ ด้านซ้าย)

```bash
curl 'localhost:5001/api/summary?minutes=60' > summary.json
```
"""),
    code("""
#@title (ไม่บังคับ) วิเคราะห์ summary.json ที่อัปโหลดมา
import json, os
if os.path.exists("summary.json"):
    data = json.load(open("summary.json"))
    series = data.get("series") or data.get("history") or {}
    series = {int(k): v for k, v in series.items()}
    for r in detect_anomalies(series): print(r)
else:
    print("ยังไม่มีไฟล์ summary.json: ข้ามเซลล์นี้ได้")
""", "real-data"),
]
save("anomaly_playground.ipynb", anom, gpu=False)
