"""Build the static course site into docs/ (GitHub Pages serves that folder).

    python3 tools/build_site.py

Content lives in this file as plain HTML strings so it is easy for students/teachers to edit.
"""
import html
import pathlib

DOCS = pathlib.Path(__file__).resolve().parent.parent / "docs"
REPO = "https://github.com/arefandywae-lab/aiot-cucumber-classroom"

NAV = [
    ("index.html", "หน้าแรก"),
    ("lessons/0-start.html", "0 เริ่มต้นกับ AIoT"),
    ("lessons/1-sensors.html", "1 เซนเซอร์วัดอะไรได้"),
    ("lessons/2-board.html", "2 ต่อบอร์ด Cucumber"),
    ("lessons/3-gateway.html", "3 ส่งข้อมูลผ่าน MQTT"),
    ("lessons/4-ui.html", "4 หน้าเว็บและ Telegram"),
    ("lessons/5-ai-anomaly.html", "5 AI ตรวจความผิดปกติ"),
    ("lessons/6-ai-chat.html", "6 AI แชทบน Colab"),
    ("teachers.html", "สำหรับครู"),
    ("ai-workflow.html", "ทำงานกับ AI อย่างไร"),
]


def code(text):
    return f"<pre><code>{html.escape(text.strip(chr(10)))}</code></pre>"


def page(path, title, body):
    depth = path.count("/")
    root = "../" * depth
    links = "".join(
        f'<a href="{root}{href}"{" class=on" if href == path else ""}>{html.escape(label)}</a>' for href, label in NAV)
    out = f"""<!doctype html>
<html lang="th"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)} · AIoT Cucumber Classroom</title>
<link rel="stylesheet" href="{root}assets/style.css"></head>
<body><nav><div class="brand">🥒 AIoT Cucumber<br><small>Classroom</small></div>{links}
<a class="ext" href="{REPO}">โค้ดบน GitHub ↗</a></nav>
<main><h1>{title}</h1>{body}</main></body></html>"""
    target = DOCS / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(out, encoding="utf-8")


def step_nav(prev_href, next_href):
    parts = []
    if prev_href:
        parts.append(f'<a href="{prev_href}">← บทก่อนหน้า</a>')
    if next_href:
        parts.append(f'<a href="{next_href}" style="margin-left:auto">บทถัดไป →</a>')
    return '<div class="steps">' + "".join(parts) + "</div>"


# ----------------------------------------------------------------------------- home
page("index.html", "AIoT Cucumber Classroom", f"""
<p class="lead">เรียนรู้ AIoT แบบลงมือทำ: ให้บอร์ด <b>Cucumber</b> วัดอุณหภูมิ ความชื้น และความดันอากาศ
ส่งข้อมูลขึ้นหน้าเว็บ/Telegram แล้วให้ <b>AI</b> ช่วยบอกว่าอะไรผิดปกติ และตอบคำถามเป็นภาษาไทย</p>
<p>เหมาะกับ <b>นักเรียนมัธยมปลาย</b> (ไม่ต้องเคยเขียนโปรแกรมมาก่อน) ใช้เวลาประมาณ 3 ชั่วโมง</p>

<h2>ระบบทำงานอย่างไร</h2>
<div class="flow">
  <div>🌡 <b>บอร์ด Cucumber</b><small>อ่านเซนเซอร์ทุก 3 วินาที</small></div><span>→ WiFi/MQTT →</span>
  <div>🖥 <b>Gateway</b><small>เก็บข้อมูล + API (Docker)</small></div><span>→</span>
  <div>🤖 <b>AI</b><small>ตรวจผิดปกติ + แชท LLM (Colab)</small></div><span>→</span>
  <div>📱 <b>UI</b><small>หน้าเว็บ หรือ Telegram</small></div>
</div>

<h2>ลองใช้งานหน้าเว็บ</h2>
<p>หน้าเว็บนี้เชื่อมกับ gateway ของคุณเอง ใส่ URL ของ gateway (เช่นจาก ngrok) แล้วกดเปิด
ถ้ายังไม่มี gateway ให้ทำบทที่ 3 ก่อน</p>
<form class="launch" onsubmit="event.preventDefault();var u=this.api.value.trim();location.href='app/'+(u?'?api='+encodeURIComponent(u):'');">
  <input name="api" placeholder="https://xxxx.ngrok-free.app" aria-label="URL ของ gateway">
  <button>เปิดหน้าเว็บ</button>
</form>

<h2>บทเรียน</h2>
<ol class="toc">
  <li><a href="lessons/0-start.html">เริ่มต้นกับ AIoT</a> — IoT คืออะไร AI เข้ามาช่วยตรงไหน</li>
  <li><a href="lessons/1-sensors.html">เซนเซอร์วัดอะไรได้</a> — BMP280 และ HTS221</li>
  <li><a href="lessons/2-board.html">ต่อบอร์ด Cucumber</a> — อัปโหลดโปรแกรมลงบอร์ด</li>
  <li><a href="lessons/3-gateway.html">ส่งข้อมูลผ่าน MQTT</a> — เปิด gateway ด้วย Docker</li>
  <li><a href="lessons/4-ui.html">หน้าเว็บและ Telegram</a> — ดูข้อมูลบนมือถือ</li>
  <li><a href="lessons/5-ai-anomaly.html">AI ตรวจความผิดปกติ</a> — สถิติ z-score</li>
  <li><a href="lessons/6-ai-chat.html">AI แชทบน Colab</a> — ถามบอร์ดเป็นภาษาไทย</li>
</ol>

<h2>ตัวเลือกตามอุปกรณ์ที่มี</h2>
<table>
<tr><th></th><th>ตัวเลือก</th></tr>
<tr><td>ไม่มีบอร์ด</td><td>ใช้ <code>devices/simulator.py</code> ส่งข้อมูลจำลองเข้า gateway แทนบอร์ด</td></tr>
<tr><td>AI ไม่ต้องใช้อินเทอร์เน็ต</td><td>ตัวตรวจผิดปกติและคำตอบแบบกฎง่ายๆ ทำงานบนเครื่องเอง ไม่ต้องมี LLM</td></tr>
<tr><td>AI แบบ LLM</td><td>รันบน Google Colab (ไม่ต้องมี GPU เอง) หรือรัน Ollama บนคอมพิวเตอร์เอง</td></tr>
<tr><td>UI</td><td>หน้าเว็บของโปรเจกต์ หรือ Telegram Mini App ใช้ gateway ตัวเดียวกัน</td></tr>
</table>
""")

# ----------------------------------------------------------------------------- lesson 0
page("lessons/0-start.html", "0 เริ่มต้นกับ AIoT", """
<p><b>IoT</b> (Internet of Things) คือสิ่งของที่มีเซนเซอร์และต่อเน็ตได้ ส่วน <b>AI</b> คือโปรแกรมที่ "เรียนรู้หรือตัดสินใจ" จากข้อมูล
เมื่อรวมกันเป็น <b>AIoT</b> เราจะได้ระบบที่ไม่ได้แค่วัดค่า แต่ช่วยตีความให้ด้วย</p>
<h2>เราจะสร้างอะไร</h2>
<ul>
<li>สถานีวัดอากาศในห้องเรียน อ่านค่าทุก 3 วินาที</li>
<li>หน้าเว็บ/Telegram แสดงค่าและกราฟ</li>
<li>AI 2 แบบ: (1) ตรวจว่าค่าผิดปกติไหม (2) ตอบคำถามเช่น "ตอนนี้ร้อนไหม"</li>
</ul>
<h2>ของที่ต้องมี</h2>
<table>
<tr><th>รายการ</th><th>หมายเหตุ</th></tr>
<tr><td>บอร์ด Cucumber R (ESP32-S2) พร้อมเซนเซอร์ BMP280, HTS221</td><td>ไม่มีก็ใช้ตัวจำลองได้</td></tr>
<tr><td>คอมพิวเตอร์ (Mac/Windows/Linux) ติดตั้ง Docker และ Python 3.10+</td><td>ใช้เป็น gateway</td></tr>
<tr><td>WiFi 2.4 GHz ที่บอร์ดและคอมพิวเตอร์อยู่วงเดียวกัน</td><td>บอร์ดต่อ 5 GHz ไม่ได้</td></tr>
<tr><td>บัญชี Google (สำหรับ Colab) และ Telegram (ถ้าอยากใช้บนมือถือ)</td><td>ไม่บังคับ</td></tr>
</table>
<h2>ดาวน์โหลดโปรเจกต์</h2>
""" + code("git clone https://github.com/arefandywae-lab/aiot-cucumber-classroom\ncd aiot-cucumber-classroom") +
     step_nav("", "1-sensors.html"))

# ----------------------------------------------------------------------------- lesson 1
page("lessons/1-sensors.html", "1 เซนเซอร์วัดอะไรได้", """
<p>เซนเซอร์คือ "ประสาทสัมผัส" ของบอร์ด แปลงสิ่งที่เกิดขึ้นจริง (ความร้อน ความชื้น แรงดัน) ให้เป็นตัวเลข</p>
<table>
<tr><th>เซนเซอร์</th><th>วัดอะไร</th><th>รหัส node</th></tr>
<tr><td>BMP280</td><td>อุณหภูมิ (°C)</td><td>1</td></tr>
<tr><td>BMP280</td><td>ความดันอากาศ (hPa)</td><td>2</td></tr>
<tr><td>HTS221</td><td>อุณหภูมิ (°C)</td><td>3</td></tr>
<tr><td>HTS221</td><td>ความชื้นสัมพัทธ์ (%)</td><td>4</td></tr>
</table>
<h2>ความหมายของตัวเลข</h2>
<ul>
<li><b>ความดันอากาศ</b> ปกติราว 1010 hPa ถ้าลดลงเร็วมักเป็นสัญญาณว่าฝนกำลังจะมา</li>
<li><b>ความชื้นสัมพัทธ์</b> บอกว่าอากาศอุ้มไอน้ำอยู่กี่เปอร์เซ็นต์ของที่อุ้มได้สูงสุด ยิ่งชื้นยิ่งรู้สึกร้อนอบอ้าว</li>
</ul>
<div class="try"><b>ลองทำ</b> เอามือกุมเซนเซอร์หรือเป่าลมใส่ แล้วดูว่าค่าไหนเปลี่ยนก่อน เพราะอะไร</div>
<h2>เซนเซอร์สองตัววัดอุณหภูมิเหมือนกัน ค่าตรงกันไหม</h2>
<p>มักต่างกันเล็กน้อย (ไม่เกิน 1 °C) นี่คือเรื่องจริงของงานวัด: เซนเซอร์ทุกตัวมีความคลาดเคลื่อน
และมีสัญญาณรบกวน ซึ่งเป็นเหตุผลที่บทที่ 5 ต้องใช้สถิติช่วยตัดสินว่า "ผิดปกติ" จริงหรือแค่แกว่งตามปกติ</p>
""" + step_nav("0-start.html", "2-board.html"))

# ----------------------------------------------------------------------------- lesson 2
page("lessons/2-board.html", "2 ต่อบอร์ด Cucumber", """
<p>โปรแกรมของบอร์ดอยู่ในโฟลเดอร์ <code>devices/cucumber/</code> ใช้ PlatformIO (ปลั๊กอินของ VS Code หรือ <code>pip install platformio</code>)</p>
<h2>ขั้นที่ 1: ตั้งค่า WiFi และที่อยู่ gateway</h2>
<p>แก้ <code>devices/cucumber/include/Config.h</code> ใส่ชื่อ WiFi และ IP ของคอมพิวเตอร์ที่จะรัน gateway
(Mac: <code>ipconfig getifaddr en0</code> หรือ <code>en1</code>)</p>
""" + code('#define WIFI_SSID        "YOUR_WIFI_NAME"\n#define MQTT_BROKER_IP   "192.168.1.100"') + """
<p>คัดลอก <code>secrets.h.example</code> เป็น <code>secrets.h</code> แล้วใส่รหัส WiFi
(ไฟล์นี้ถูกกันไว้ไม่ให้ขึ้น GitHub จะได้ไม่หลุดรหัสผ่าน)</p>
<h2>ขั้นที่ 2: อัปโหลด</h2>
""" + code("cd devices/cucumber\npio run -t upload\npio device monitor") + """
<p>ใน Serial Monitor ควรเห็นบรรทัดแบบนี้ทุก 3 วินาที</p>
""" + code('[Sensor] BMP280: T=29.86 C, P=1009.86 hPa | HTS221: T=29.33 C, RH=60.34 %\n[MQTT] Published -> /cn466/data: {"node":1,"value":29.86}') + """
<h2>ถ้าไม่ขึ้น</h2>
<ul>
<li><b>อัปโหลดไม่ได้ / พอร์ตหาย</b> กดปุ่ม BOOT ค้างไว้ แล้วกด RESET หนึ่งครั้ง จากนั้นสั่งอัปโหลดใหม่</li>
<li><b>ต่อ WiFi ไม่ได้</b> ตรวจว่าเป็นคลื่น 2.4 GHz และรหัสถูกต้อง</li>
<li><b>ต่อ MQTT ไม่ได้</b> IP ใน <code>Config.h</code> ต้องตรงกับคอมพิวเตอร์ และไฟร์วอลล์ต้องไม่บล็อก port 1883</li>
</ul>
<div class="try"><b>ไม่มีบอร์ด?</b> ข้ามไปบทที่ 3 แล้วใช้ <code>python3 devices/simulator.py 30 1013 60</code> แทน (อุณหภูมิ ความดัน ความชื้น)</div>
""" + step_nav("1-sensors.html", "3-gateway.html"))

# ----------------------------------------------------------------------------- lesson 3
page("lessons/3-gateway.html", "3 ส่งข้อมูลผ่าน MQTT", """
<p><b>MQTT</b> เป็นเหมือน "ไปรษณีย์" ของ IoT: บอร์ดส่งข้อความเข้า <i>topic</i> (เหมือนตู้จดหมาย) ใครสนใจก็มา subscribe
ตัวกลางเรียกว่า <b>broker</b> (เราใช้ Mosquitto) ข้อความของเราหน้าตาแบบนี้</p>
""" + code('topic:   /cn466/data\npayload: {"node": 3, "value": 29.33}') + """
<h2>เปิด gateway ด้วย Docker</h2>
<p>gateway คือโปรแกรมที่รับข้อความ เก็บลงฐานข้อมูล และเปิด API ให้หน้าเว็บมาอ่าน</p>
""" + code("cd gateway\ncp .env.example .env     # ไม่ต้องแก้อะไรก็ใช้ได้\ndocker compose up -d --build") + """
<p>ตรวจว่าทำงาน: เปิด <code>http://localhost:5001/app</code> หรือรัน</p>
""" + code("curl localhost:5001/api/summary") + """
<table>
<tr><th>Endpoint</th><th>ทำอะไร</th></tr>
<tr><td><code>GET /api/summary</code></td><td>ค่าล่าสุดของทุก node + ข้อมูลย้อนหลังสำหรับกราฟ</td></tr>
<tr><td><code>GET /api/anomaly</code></td><td>AI ตรวจความผิดปกติ (บทที่ 5)</td></tr>
<tr><td><code>POST /api/ask</code></td><td>AI แชท (บทที่ 6)</td></tr>
</table>
<h2>port สำคัญ</h2>
<p>gateway ฟังที่ port 5000 ใน Docker แต่เรา map ออกมาเป็น <b>5001</b> บนเครื่อง เพราะ macOS ใช้ port 5000 อยู่แล้ว</p>
<div class="try"><b>ลองทำ</b> ถ้าไม่มีบอร์ด รัน <code>python3 devices/simulator.py 30 1013 60</code> แล้วดูค่าใน <code>/api/summary</code> เปลี่ยน</div>
""" + step_nav("2-board.html", "4-ui.html"))

# ----------------------------------------------------------------------------- lesson 4
page("lessons/4-ui.html", "4 หน้าเว็บและ Telegram", """
<p>หน้าเว็บ (<code>gateway/mqtt_collector/miniapp.html</code>) เขียนด้วย HTML/CSS/JavaScript ล้วน ไม่มีไลบรารีเพิ่ม
ดึงข้อมูลจาก <code>/api/summary</code> ทุก 3 วินาที แล้ววาดการ์ดกับกราฟ</p>
<h2>ทางเลือก A: เปิดในเบราว์เซอร์</h2>
<p>เปิด <code>http://localhost:5001/app</code> บนคอมพิวเตอร์ หรือถ้าอยากดูบนมือถือที่อยู่ WiFi เดียวกัน ใช้ <code>http://IP-ของคอม:5001/app</code></p>
<h2>ทางเลือก B: Telegram Mini App</h2>
<p>Telegram บังคับให้เป็น <b>https</b> เราจึงต้องมีลิงก์สาธารณะ ใช้ ngrok ทำ port forwarding:</p>
""" + code("ngrok http 5001") + """
<ol>
<li>คุยกับ <code>@BotFather</code> พิมพ์ <code>/newbot</code> เพื่อได้ token</li>
<li>ใส่ <code>TELEGRAM_BOT_TOKEN</code> และ <code>MINIAPP_URL</code> (ลิงก์ https จาก ngrok) ใน <code>gateway/.env</code></li>
<li><code>docker compose up -d mqtt_collector</code> แล้วเปิดแชทกับบอท กดปุ่ม <b>Sensors</b> หรือพิมพ์ <code>/app</code></li>
</ol>
<div class="warn"><b>ระวัง</b> token ของบอทเหมือนรหัสผ่าน อย่าส่งให้ใครหรืออัปโหลดขึ้น GitHub
ลิงก์ ngrok แบบฟรีจะเปลี่ยนทุกครั้งที่เปิดใหม่ ต้องแก้ <code>MINIAPP_URL</code> ใหม่</div>
<h2>แล้วใครเปิดหน้านี้ได้บ้าง</h2>
<p>ใครมีลิงก์ก็เปิดดูได้ แต่ Telegram จะแนบข้อมูลผู้ใช้ที่ <b>เซ็นลายเซ็นไว้</b> มาด้วย gateway ตรวจลายเซ็นนั้นที่ <code>/api/verify</code>
(ดูฟังก์ชัน <code>check_init_data</code> ใน <code>rest_app.py</code>) เพื่อรู้ว่าเปิดมาจาก Telegram จริง</p>
<h2>ใช้หน้าเว็บจาก GitHub Pages</h2>
<p>หน้าเว็บชุดเดียวกันอยู่ที่ <code>app/</code> ของเว็บนี้ ต่อกับ gateway ของคุณผ่านพารามิเตอร์ <code>?api=</code> เช่น
<code>app/?api=https://xxxx.ngrok-free.app</code></p>
""" + step_nav("3-gateway.html", "5-ai-anomaly.html"))

# ----------------------------------------------------------------------------- lesson 5
page("lessons/5-ai-anomaly.html", "5 AI ตรวจความผิดปกติ", """
<p>AI ไม่จำเป็นต้องเป็นโมเดลยักษ์ แค่ <b>สถิติ</b> ก็ตรวจความผิดปกติของเซนเซอร์ได้ และอธิบายให้เข้าใจได้ทุกขั้น</p>
<h2>ไอเดีย</h2>
<ol>
<li>เก็บค่าย้อนหลัง 60 นาที แบ่งเป็น <b>ช่วงอ้างอิง</b> (80% แรก) กับ <b>ช่วงล่าสุด</b> (20% หลัง)</li>
<li>หาค่าเฉลี่ย (mean) และความแกว่งปกติ (std) ของช่วงอ้างอิง</li>
<li>คำนวณ <b>z = (เฉลี่ยช่วงล่าสุด − เฉลี่ยช่วงอ้างอิง) ÷ std</b></li>
<li>ถ้า |z| มากกว่า 3 แปลว่าค่าห่างจากปกติมาก ให้เตือน</li>
</ol>
<h2>ตัวอย่างคิดมือ</h2>
<p>ปกติอุณหภูมิ 30.0 °C แกว่ง ±0.2 แล้วค่าล่าสุดเฉลี่ย 31.0 °C → z = (31.0 − 30.0) ÷ 0.2 = <b>5</b> มากกว่า 3 → เตือน
แต่ถ้าล่าสุด 30.3 °C → z = 1.5 ยังปกติ</p>
<p>โค้ดจริงอยู่ที่ <code>detect_anomalies()</code> ใน <code>gateway/mqtt_collector/ai_helpers.py</code> เรียกดูผลได้ที่</p>
""" + code("curl 'localhost:5001/api/anomaly?minutes=60'") + """
<figure><img src="../assets/ui-simulated.png" alt="หน้าเว็บแสดงป้ายเตือนอุณหภูมิสูงผิดปกติ" style="max-width:320px;border-radius:12px;border:1px solid var(--line)">
<figcaption><small>ภาพตัวอย่างจาก <b>ข้อมูลจำลอง</b> (ส่ง 40 ค่าปกติ ตามด้วย 10 ค่าที่อุณหภูมิสูงขึ้น) ป้าย AI เตือนทั้งอุณหภูมิและความชื้น</small></figcaption></figure>
<h2>ลองทำ</h2>
<ol>
<li>เปิดหน้าเว็บ ให้บอร์ดทำงานอย่างน้อย 10 นาทีเพื่อให้มีข้อมูลอ้างอิง</li>
<li>เอาไดร์เป่าผมเป่าใส่เซนเซอร์ (ห่างๆ) 1–2 นาที แล้วดูป้าย AI</li>
<li>ลองเปลี่ยน <code>z_limit</code> จาก 3 เป็น 2 แล้วทดสอบอีกครั้ง เตือนไวขึ้นหรือช้าลง มีเตือนผิดบ่อยขึ้นไหม</li>
</ol>
<div class="try"><b>คิดต่อ</b> ทำไมต้องกำหนดค่า std ขั้นต่ำ (<code>MIN_STD</code>) ถ้าไม่กำหนด แล้วห้องเงียบมากจนค่าแทบไม่แกว่ง จะเกิดอะไรขึ้น</div>
<h2>ข้อจำกัด</h2>
<p>วิธีนี้เทียบกับ "เมื่อกี้" เท่านั้น ถ้าอุณหภูมิค่อยๆ เพิ่มช้ามากทั้งวันจะไม่เตือน และถ้าช่วงอ้างอิงมีเหตุการณ์ผิดปกติปนอยู่ ค่า std จะบวม ทำให้ตรวจไม่ไว
นี่คือสิ่งที่ AI ทุกแบบมี: ทำงานได้ดีภายใต้สมมติฐานบางอย่าง</p>
""" + step_nav("4-ui.html", "6-ai-chat.html"))

# ----------------------------------------------------------------------------- lesson 6
page("lessons/6-ai-chat.html", "6 AI แชทบน Colab", """
<p>AI แบบที่สองคือ <b>LLM</b> (โมเดลภาษาขนาดใหญ่) ที่อ่านค่าเซนเซอร์ล่าสุดแล้วตอบคำถามเป็นภาษาไทย เช่น "ตอนนี้ร้อนไหม" "มีอะไรผิดปกติหรือเปล่า"</p>
<h2>เลือกที่รัน AI</h2>
<table>
<tr><th>ที่รัน</th><th>เหมาะกับ</th><th>วิธี</th></tr>
<tr><td>Google Colab</td><td>เครื่องไม่แรง ไม่มี GPU</td><td>เปิดโน้ตบุ๊ก <code>ai/colab/cucumber_llm.ipynb</code> เลือก GPU T4 รันทุกเซลล์ จะได้ลิงก์ <code>trycloudflare.com</code></td></tr>
<tr><td>คอมพิวเตอร์เอง</td><td>มี RAM ≥ 8 GB</td><td>ติดตั้ง Ollama แล้ว <code>ollama pull qwen2.5:3b</code> ใช้ <code>OLLAMA_URL=http://host.docker.internal:11434</code></td></tr>
<tr><td>ไม่รัน LLM</td><td>ไม่มีเน็ต/ไม่อยากตั้งค่า</td><td>เว้น <code>OLLAMA_URL</code> ว่าง ระบบตอบด้วยกฎง่ายๆ</td></tr>
</table>
<p>เมื่อได้ลิงก์ ใส่ใน <code>gateway/.env</code> แล้วรีสตาร์ท</p>
""" + code("OLLAMA_URL=https://xxxx.trycloudflare.com\nOLLAMA_MODEL=qwen2.5:3b") + code("docker compose up -d mqtt_collector") + """
<h2>มันตอบจากอะไร</h2>
<p>gateway ไม่ได้ให้ LLM "เดา" แต่ส่งค่าเซนเซอร์ล่าสุดและผลตรวจผิดปกติไปในคำถามด้วย (เรียกว่า <i>grounding</i>)
พร้อมคำสั่งให้ตอบจากข้อมูลที่ให้เท่านั้น ใต้คำตอบจะบอกเสมอว่า "ตอบโดย LLM" หรือ "ตอบโดยกฎง่ายๆ"</p>
<div class="try"><b>ลองทำ</b> ถามว่า "ตอนนี้ร้อนไหม" "ความชื้นเท่าไหร่" "พรุ่งนี้ฝนตกไหม" แล้วสังเกตว่าคำถามสุดท้ายโมเดลควรบอกว่าข้อมูลไม่พอ ไม่ใช่เดาตัวเลข</div>
<div class="warn"><b>ระวัง</b> ลิงก์ Colab ใครได้ไปก็ใช้โมเดลของคุณได้ อย่าแชร์ต่อ และ LLM ตอบผิดได้ ใช้ช่วยอธิบายเท่านั้น
อย่าใช้ตัดสินใจเรื่องความปลอดภัย</div>
""" + step_nav("5-ai-anomaly.html", ""))

# ----------------------------------------------------------------------------- teachers
page("teachers.html", "สำหรับครู", """
<h2>แผนการสอน 3 ชั่วโมง</h2>
<table>
<tr><th>เวลา</th><th>กิจกรรม</th><th>บท</th></tr>
<tr><td>20 นาที</td><td>บรรยายสั้น: IoT/AI คืออะไร ดูตัวอย่างหน้าเว็บ</td><td>0–1</td></tr>
<tr><td>40 นาที</td><td>อัปโหลดโปรแกรมลงบอร์ด ดูค่าใน Serial Monitor</td><td>2</td></tr>
<tr><td>30 นาที</td><td>เปิด gateway ดูข้อมูลบนหน้าเว็บ/Telegram</td><td>3–4</td></tr>
<tr><td>40 นาที</td><td>กิจกรรม z-score: เป่าไดร์ ปรับ <code>z_limit</code> แล้วสังเกต</td><td>5</td></tr>
<tr><td>30 นาที</td><td>ถาม LLM ทดสอบคำถามที่ตอบได้/ไม่ได้ อภิปรายข้อจำกัด</td><td>6</td></tr>
<tr><td>20 นาที</td><td>สรุป ตอบคำถาม</td><td></td></tr>
</table>
<h2>เตรียมก่อนคาบ</h2>
<ul>
<li>รัน gateway หนึ่งเครื่องต่อกลุ่ม (หรือหนึ่งเครื่องทั้งห้อง) และเช็กว่า WiFi 2.4 GHz ใช้ได้</li>
<li>ถ้าห้องมี WiFi ที่บล็อกอุปกรณ์คุยกัน ให้ใช้ฮอตสปอตมือถือแทน</li>
<li>เตรียม <code>devices/simulator.py</code> ไว้ให้กลุ่มที่บอร์ดไม่พอ</li>
<li>เปิด Colab ล่วงหน้า 10 นาที โมเดลโหลดครั้งแรกใช้เวลา</li>
</ul>
<h2>เกณฑ์ประเมินเสนอ</h2>
<ul>
<li>อธิบายได้ว่าข้อมูลเดินทางจากบอร์ดไปหน้าเว็บอย่างไร (วาดแผนภาพ)</li>
<li>อธิบายได้ว่า z-score บอกอะไร และตั้ง <code>z_limit</code> แล้วเกิดอะไรขึ้น</li>
<li>ยกตัวอย่างคำถามที่ LLM ควรปฏิเสธ/บอกว่าไม่รู้ พร้อมเหตุผล</li>
</ul>
<h2>ปัญหาที่เจอบ่อย</h2>
<table>
<tr><th>อาการ</th><th>สาเหตุ/วิธีแก้</th></tr>
<tr><td>หน้าเว็บไม่มีค่า</td><td>บอร์ดยังไม่ต่อ WiFi/MQTT: ดู Serial Monitor และตรวจ IP ใน <code>Config.h</code></td></tr>
<tr><td><code>docker</code> ค้าง</td><td>Docker Desktop ยังไม่พร้อม หรือดิสก์เต็ม: รีสตาร์ท Docker และเคลียร์พื้นที่</td></tr>
<tr><td>Telegram เปิดหน้าเปล่า</td><td><code>MINIAPP_URL</code> ต้องเป็น https และลิงก์ ngrok ยังไม่หมดอายุ</td></tr>
<tr><td>AI ตอบ "กฎง่ายๆ" ตลอด</td><td>ลิงก์ Colab หมดอายุหรือยังไม่ได้ใส่ <code>OLLAMA_URL</code></td></tr>
</table>
<h2>ความปลอดภัยและข้อมูลส่วนบุคคล</h2>
<ul>
<li>Mosquitto ในโปรเจกต์เปิดแบบไม่ต้องล็อกอิน เหมาะกับห้องเรียนเท่านั้น อย่าเปิด port 1883 สู่อินเทอร์เน็ต</li>
<li>เก็บ token/รหัส WiFi ใน <code>.env</code> และ <code>secrets.h</code> ซึ่งไม่ถูกอัปโหลดขึ้น GitHub</li>
<li>ข้อมูลที่เก็บเป็นค่าสภาพอากาศเท่านั้น ไม่มีข้อมูลระบุตัวบุคคล</li>
</ul>
""")

# ----------------------------------------------------------------------------- AI workflow
page("ai-workflow.html", "ทำงานกับ AI อย่างไร (flow สั่งงานและตรวจงาน)", f"""
<p>โปรเจกต์นี้พัฒนาโดยมี AI (Claude Code) เป็นผู้ช่วยเขียนโค้ดและเอกสาร ส่วนนี้สรุป <b>วิธีสั่งและวิธีตรวจ</b>
เพราะการเชื่อผลของ AI โดยไม่ตรวจเป็นความเสี่ยงที่ใหญ่ที่สุด</p>
<div class="flow">
  <div><b>1 กำหนดโจทย์</b><small>เป้าหมาย กลุ่มเป้าหมาย ข้อจำกัด</small></div><span>→</span>
  <div><b>2 ให้ AI สำรวจ</b><small>อ่านโค้ด/ตัวอย่างที่มี ก่อนเขียน</small></div><span>→</span>
  <div><b>3 ให้ AI ลงมือ</b><small>ทีละชิ้นเล็กๆ</small></div><span>→</span>
  <div><b>4 ตรวจ</b><small>เทสต์ + ของจริง</small></div><span>→</span>
  <div><b>5 แก้/ถามต่อ</b><small>วนกลับ</small></div>
</div>
<h2>ตัวอย่างการสั่งงานจริงในโปรเจกต์นี้</h2>
<table>
<tr><th>ขั้น</th><th>สิ่งที่สั่ง</th><th>สิ่งที่ตรวจ</th></tr>
<tr><td>กำหนดโจทย์</td><td>ส่งข้อกำหนดงาน + เลือก: กลุ่มเป้าหมาย ม.ปลาย, AI ทั้งตรวจผิดปกติและแชท, ใช้ Colab, UI ทั้งเว็บและ Telegram</td><td>เลือกเองทุกข้อ ไม่ปล่อยให้ AI เดา</td></tr>
<tr><td>สำรวจ</td><td>"ดูไฟล์ใน demo_05_iot ว่ามีอะไรให้ใช้ซ้ำ"</td><td>เช็กว่ามี token/รหัสผ่านติดไฟล์ไหมก่อนขึ้น GitHub</td></tr>
<tr><td>เขียนโค้ด AI</td><td>สร้าง <code>ai_helpers.py</code> (z-score + แชท + fallback)</td><td>เขียน unit test 6 ข้อ รันผ่าน (<code>pytest tests</code>)</td></tr>
<tr><td>ทดสอบจริง</td><td>แฟลชบอร์ด รัน Docker เปิด Telegram</td><td>ดู Serial Monitor, log ของ broker, หน้าจอ Telegram จริง</td></tr>
<tr><td>ส่วนที่ทำไม่ได้</td><td>Colab notebook</td><td>AI ไม่มีบัญชี Colab ให้ทดสอบ จึงบอกตรงๆ ว่ายังไม่ได้รันจริง ให้ครูลองก่อนใช้</td></tr>
</table>
<h2>กฎที่ใช้ตรวจงาน AI</h2>
<ol>
<li><b>ให้ AI บอกว่าทดสอบอะไรไปแล้ว/ยังไม่ได้ทดสอบอะไร</b> และไม่เชื่อคำว่า "น่าจะใช้ได้"</li>
<li><b>ของที่มีผลภายนอกต้องถามก่อน</b> เช่น เขียนทับโปรแกรมในบอร์ด (AI ถามก่อนแฟลช) หรืออัปโหลดขึ้นอินเทอร์เน็ต</li>
<li><b>ความลับไม่ผ่านแชท/ไม่ขึ้น GitHub</b> ใช้ <code>.env</code> และ <code>.gitignore</code></li>
<li><b>ให้ AI อธิบายโค้ดที่เขียน</b> ถ้าอธิบายให้เพื่อนฟังไม่ได้ แปลว่ายังไม่เข้าใจพอจะส่งงาน</li>
<li><b>เปิดดูของจริง</b> ตัวเลขจากบอร์ด หน้าจอจริง ไม่ใช่แค่ดูข้อความที่ AI รายงาน</li>
</ol>
<h2>โครงสร้างโปรเจกต์</h2>
""" + code("""devices/      โปรแกรมบอร์ด Cucumber + ตัวจำลองข้อมูล
gateway/      Docker: Mosquitto + REST API + หน้าเว็บ/Telegram
ai/colab/     โน้ตบุ๊กรัน LLM บน Colab
docs/         เว็บคอร์สนี้ (GitHub Pages) สร้างจาก tools/build_site.py
tests/        unit test ของส่วน AI"""))

print("built", len(list(DOCS.rglob("*.html"))), "pages")
