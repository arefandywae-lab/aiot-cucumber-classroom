"""Build the static course site into docs/ (GitHub Pages serves that folder).

    python3 tools/build_site.py

Content lives in this file as plain HTML strings so it is easy for students/teachers to edit.
"""
import html
import pathlib
import re

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
    ("setup.html", "เตรียมเครื่องมือ"),
    ("applications.html", "นำไปประยุกต์ใช้"),
    ("no-board.html", "ไม่มีบอร์ด ใช้ตัวจำลอง"),
    ("challenges.html", "ปรับแก้และต่อยอด"),
    ("troubleshooting.html", "แก้ปัญหา"),
    ("security.html", "ความปลอดภัย"),
    ("references.html", "แหล่งอ้างอิง"),
]


OWNER, NAME = REPO.rstrip("/").split("/")[-2:]
COLAB = f"https://colab.research.google.com/github/{OWNER}/{NAME}/blob/main/ai/colab/"
COLAB_ICON = '<svg width="22" height="22" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M16.9 5.1a7 7 0 0 0-9.8 0l1.7 1.7a4.6 4.6 0 0 1 6.4 0l1.7-1.7Zm-9.8 13.8a7 7 0 0 0 9.8 0l-1.7-1.7a4.6 4.6 0 0 1-6.4 0l-1.7 1.7ZM5.1 7.1a7 7 0 0 0 0 9.8l1.7-1.7a4.6 4.6 0 0 1 0-6.4L5.1 7.1Zm13.8 9.8a7 7 0 0 0 0-9.8l-1.7 1.7a4.6 4.6 0 0 1 0 6.4l1.7 1.7Z"/></svg>'


def colab_btn(nb, label, alt=False):
    return f'<a class="colab{" alt" if alt else ""}" href="{COLAB}{nb}" target="_blank" rel="noopener">{COLAB_ICON}{label}</a>'


def quiz(*qa):
    """Self-check questions: (question, answer) pairs, answers hidden in <details>."""
    return "<h2>ทบทวน</h2>" + "".join(
        f'<details class="ans"><summary>{q}</summary><p>{a}</p></details>' for q, a in qa)


def code(text):
    return f"<pre><code>{html.escape(text.strip(chr(10)))}</code></pre>"


BRAND = ('<svg class="mark" viewBox="0 0 32 32" aria-hidden="true"><g transform="rotate(-28 16 16)">'
         '<rect x="2" y="11.5" width="28" height="9" rx="4.5" fill="currentColor"/>'
         '<circle cx="10" cy="16" r="1.2" fill="var(--paper)"/><circle cx="16" cy="16" r="1.2" fill="var(--paper)"/>'
         '<circle cx="22" cy="16" r="1.2" fill="var(--paper)"/></g></svg>')
FONTS = ("https://fonts.googleapis.com/css2?family=Anuphan:wght@500;700&family=IBM+Plex+Sans+Thai:wght@400;600"
         "&family=IBM+Plex+Mono:wght@400;500&display=swap")


def page(path, title, body, home=False):
    depth = path.count("/")
    root = "../" * depth
    links = "".join(
        f'<a href="{root}{href}"{" class=on" if href == path else ""}>{html.escape(label)}</a>' for href, label in NAV)
    if home:
        head = ""
    else:
        m = re.match(r"(\d+)\s+(.*)", title)
        head = (f'<header class="ph"><p class="no">บทที่ {m.group(1)}</p><h1>{html.escape(m.group(2))}</h1></header>'
                if m else f'<header class="ph"><h1>{html.escape(title)}</h1></header>')
    play_js = f'<script src="{root}assets/play.js" defer></script>' if "data-play" in body else ""
    out = f"""<!doctype html>
<html lang="th"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)} · AIoT Cucumber Classroom</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONTS}">
<link rel="stylesheet" href="{root}assets/style.css">
<script>document.documentElement.classList.add('js')</script></head>
<body><div class="bar"></div><nav><a class="brand" href="{root}index.html">{BRAND}<span>AIoT Cucumber<small>Classroom</small></span></a>{links}
<a class="ext" href="{REPO}">โค้ดบน GitHub ↗</a></nav>
<main{' class="home"' if home else ''}>{head}{body}</main><script src="{root}assets/fx.js" defer></script>{play_js}</body></html>"""
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
LESSONS = [
    ("0", "เริ่มต้นกับ AIoT", "IoT คืออะไร AI เข้ามาช่วยตรงไหน", "lessons/0-start.html", False),
    ("1", "เซนเซอร์วัดอะไรได้", "BMP280 และ HTS221 แปลงความร้อน ความชื้น แรงดัน เป็นตัวเลข", "lessons/1-sensors.html", False),
    ("2", "ต่อบอร์ด Cucumber", "อัปโหลดโปรแกรมลงบอร์ดและอ่านค่าใน Serial Monitor", "lessons/2-board.html", False),
    ("3", "ส่งข้อมูลผ่าน MQTT", "เปิด gateway ด้วย Docker ให้รับและเก็บข้อมูล", "lessons/3-gateway.html", False),
    ("4", "หน้าเว็บและ Telegram", "ดูค่าและกราฟบนมือถือ", "lessons/4-ui.html", False),
    ("5", "AI ตรวจความผิดปกติ", "สถิติ z-score ที่คิดมือตามได้ทุกขั้น", "lessons/5-ai-anomaly.html", True),
    ("6", "AI แชทบน Colab", "ถามบอร์ดเป็นภาษาไทยว่าตอนนี้ร้อนไหม", "lessons/6-ai-chat.html", True),
]
STACK = "".join(
    f'<article class="lcard{" ai" if ai else ""}" style="--i:{i}"><span class="no">{n}</span>'
    f'<h3>{t}</h3><p>{d}</p><a class="go" href="{h}">เปิดบทที่ {n}</a></article>'
    for i, (n, t, d, h, ai) in enumerate(LESSONS))
TICKER = "".join(f"<span>{x}</span>" for x in [
    "<b>BMP280</b> T 29.86 °C", "<b>BMP280</b> P 1009.86 hPa", "<b>HTS221</b> T 29.33 °C", "<b>HTS221</b> RH 60.34 %",
    "topic /cn466/data", "อ่านค่าทุก 3 วินาที", "<b>z</b> = (ล่าสุด − อ้างอิง) ÷ std"])

page("index.html", "AIoT Cucumber Classroom", """
<section class="hero">
  <canvas id="ascii" aria-hidden="true"></canvas>
  <div class="hero-in">
    <p class="kicker">AIoT Cucumber Classroom</p>
    <h1>ให้บอร์ดวัดอากาศ แล้วให้ AI บอกว่าอะไรผิดปกติ</h1>
    <p class="lead">เรียนรู้ AIoT แบบลงมือทำ: บอร์ด <b>Cucumber</b> วัดอุณหภูมิ ความชื้น และความดันอากาศ
    ส่งข้อมูลขึ้นหน้าเว็บหรือ Telegram จากนั้น <b>AI</b> ตรวจความผิดปกติและตอบคำถามเป็นภาษาไทย</p>
    <p class="meta">สำหรับนักเรียนมัธยมปลาย ไม่ต้องเคยเขียนโปรแกรม ใช้เวลาประมาณ 3 ชั่วโมง</p>
    <p class="cta"><a class="btn solid mag" href="lessons/0-start.html">เริ่มที่บทที่ 0</a><a class="btn mag" href="#try">เปิดหน้าเว็บ</a></p>
  </div>
  <p class="heat" id="heat" aria-hidden="true">ลองเลื่อนเมาส์บนพื้นหลัง (ค่าจำลอง)<br>เซนเซอร์เสมือน <b>29.9 °C</b></p>
</section>
<div class="mq" aria-hidden="true"><div class="track">""" + TICKER + """</div></div>

<section class="sec">
  <p class="lab">00 · โจทย์</p>
  <h2>ถ้าโรงเรือนแตงกวาร้อนเกินไปตอนไม่มีใครอยู่ จะรู้ได้อย่างไร</h2>
  <p>แตงกวาเป็นพืชที่ไวต่ออุณหภูมิและความชื้น ถ้าร้อนจัดหรืออากาศชื้นผิดปกติแล้วไม่มีใครเห็นทัน ผลผลิตเสียหายได้
  เราใช้บอร์ด <b>Cucumber</b> เป็นสถานีวัดอากาศในโรงเรือน ให้ <b>AI</b> คอยบอกว่าตอนนี้ผิดปกติหรือไม่ และตอบคำถามเป็นภาษาไทย
  รูปแบบเดียวกันนี้ใช้กับห้องเรียน ห้องเก็บของ หรือห้องเซิร์ฟเวอร์ได้ ดู <a href="applications.html">นำไปประยุกต์ใช้</a></p>
</section>

<section class="sec">
  <p class="lab">01 · ภาพรวม</p>
  <h2>ข้อมูลเดินทางจากบอร์ดถึงหน้าจออย่างไร</h2>
  <p>เลื่อนลงเพื่อดูแพ็กเก็ตข้อมูลเดินทางผ่านแต่ละขั้น</p>
  <div class="pipe">
    <div class="rail"></div><div class="fill"></div><div class="pkt"></div>
    <div class="stage"><span class="n">01</span><h3>บอร์ด Cucumber</h3><p>อ่านเซนเซอร์ทุก 3 วินาที</p><span class="via">ส่งผ่าน WiFi / MQTT</span></div>
    <div class="stage"><span class="n">02</span><h3>Gateway</h3><p>เก็บข้อมูลและเปิด API (Docker)</p><span class="via">ส่งต่อให้ AI</span></div>
    <div class="stage"><span class="n">03</span><h3>AI</h3><p>ตรวจผิดปกติ และแชท LLM บน Colab</p><span class="via">ส่งคำตอบกลับ</span></div>
    <div class="stage"><span class="n">04</span><h3>หน้าจอ</h3><p>หน้าเว็บ หรือ Telegram Mini App</p><span class="via">นักเรียนเห็นผล</span></div>
  </div>
</section>

<section class="sec">
  <p class="lab">02 · บทเรียน</p>
  <h2>เจ็ดบท เรียงซ้อนกันไปทีละบท</h2>
</section>
<div class="stack">""" + STACK + """</div>

<section class="sec" id="try">
  <p class="lab">03 · ลองใช้งาน</p>
  <h2>เปิดหน้าเว็บที่เชื่อมกับ gateway ของคุณ</h2>
  <p>ใส่ URL ของ gateway (เช่นจาก ngrok) แล้วกดเปิด ถ้ายังไม่มี gateway ให้ทำบทที่ 3 ก่อน</p>
  <form class="launch" onsubmit="event.preventDefault();var u=this.api.value.trim();location.href='app/'+(u?'?api='+encodeURIComponent(u):'');">
    <input name="api" placeholder="https://xxxx.ngrok-free.app" aria-label="URL ของ gateway">
    <button class="btn solid">เปิดหน้าเว็บ</button>
  </form>
</section>

<section class="sec">
  <p class="lab">04 · ตัวเลือก</p>
  <h2>เลือกตามอุปกรณ์ที่มี</h2>
  <dl class="opts">
    <div><dt>ไม่มีบอร์ด</dt><dd>ใช้ <code>devices/simulator.py</code> ส่งข้อมูลจำลองเข้า gateway แทนบอร์ด</dd></div>
    <div><dt>AI ไม่ต้องใช้อินเทอร์เน็ต</dt><dd>ตัวตรวจผิดปกติและคำตอบแบบกฎง่ายๆ ทำงานบนเครื่องเอง ไม่ต้องมี LLM</dd></div>
    <div><dt>AI แบบ LLM</dt><dd>รันบน Google Colab (ไม่ต้องมี GPU เอง) หรือรัน Ollama บนคอมพิวเตอร์เอง</dd></div>
    <div><dt>หน้าจอ</dt><dd>หน้าเว็บของโปรเจกต์ หรือ Telegram Mini App ใช้ gateway ตัวเดียวกัน</dd></div>
  </dl>
</section>
""", home=True)

# ----------------------------------------------------------------------------- lesson 0
page("lessons/0-start.html", "0 เริ่มต้นกับ AIoT", """
<p><b>IoT</b> (Internet of Things) คือสิ่งของที่มีเซนเซอร์และต่อเน็ตได้ ส่วน <b>AI</b> คือโปรแกรมที่ "เรียนรู้หรือตัดสินใจ" จากข้อมูล
เมื่อรวมกันเป็น <b>AIoT</b> เราจะได้ระบบที่ไม่ได้แค่วัดค่า แต่ช่วยตีความให้ด้วย</p>
<h2>โจทย์ที่เราใช้: โรงเรือนแตงกวา</h2>
<p>ลองนึกภาพโรงเรือนปลูกแตงกวาที่ไม่มีคนเฝ้าตลอดเวลา อากาศร้อนหรือชื้นผิดปกติเมื่อไหร่ เจ้าของอยากรู้ทันที
บอร์ดของเราชื่อ Cucumber ก็เหมาะกับเรื่องนี้พอดี ทุกบทต่อจากนี้คือการสร้างระบบเฝ้าดูอากาศที่ตอบโจทย์นี้ทีละชิ้น:
<b>วัดค่า</b> (บท 1–2) → <b>ส่งและเก็บ</b> (บท 3) → <b>ดูผล</b> (บท 4) → <b>AI บอกว่าผิดปกติไหม</b> (บท 5) → <b>ถามเป็นภาษาไทย</b> (บท 6)
ถ้าสนใจสถานการณ์อื่น ดู <a href="../applications.html">นำไปประยุกต์ใช้</a></p>
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
<div class="try"><b>ก่อนเริ่ม</b> ทำเช็กลิสต์ใน <a href="../setup.html">เตรียมเครื่องมือ</a> ให้ครบ (ใช้เวลาประมาณ 15 นาที)
ถ้าไม่มีบอร์ด อ่าน <a href="../no-board.html">ไม่มีบอร์ด ใช้ตัวจำลอง</a> แล้วทำต่อได้ทุกบท</div>
<h2>ภาพรวมแต่ละบท: เรียนอะไร ได้อะไร</h2>
<table>
<tr><th>บท</th><th>ได้เรียน</th><th>ลงมือทำ</th></tr>
<tr><td>1</td><td>เซนเซอร์แปลงโลกจริงเป็นตัวเลข</td><td>เลื่อนแถบค่า ดูข้อความที่บอร์ดส่ง</td></tr>
<tr><td>2</td><td>อัปโหลดโปรแกรมลงบอร์ด</td><td>ดูค่าใน Serial Monitor</td></tr>
<tr><td>3</td><td>MQTT และ gateway</td><td>เปิด Docker, เรียก API ด้วย curl</td></tr>
<tr><td>4</td><td>หน้าเว็บ/Telegram</td><td>ดูกราฟบนมือถือ</td></tr>
<tr><td>5</td><td>z-score ตรวจผิดปกติ</td><td>สนามเล่นในหน้านี้ + Colab</td></tr>
<tr><td>6</td><td>LLM ตอบคำถามจากข้อมูลจริง</td><td>เปิด Colab ด้วยปุ่มเดียว</td></tr>
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
<h2>เลื่อนดู: ค่าที่วัดกลายเป็นข้อความอย่างไร</h2>
<p>บอร์ดไม่ได้ส่ง "ภาพ" หรือ "ประโยค" แต่ส่งข้อความสั้นๆ ที่มีรหัส node กับตัวเลข ลองเลื่อนแถบแล้วดูว่าข้อความเปลี่ยนอย่างไร</p>
<div data-play="sensor"></div>
<h2>เซนเซอร์สองตัววัดอุณหภูมิเหมือนกัน ค่าตรงกันไหม</h2>
<p>มักต่างกันเล็กน้อย (ไม่เกิน 1 °C) นี่คือเรื่องจริงของงานวัด: เซนเซอร์ทุกตัวมีความคลาดเคลื่อน
และมีสัญญาณรบกวน ซึ่งเป็นเหตุผลที่บทที่ 5 ต้องใช้สถิติช่วยตัดสินว่า "ผิดปกติ" จริงหรือแค่แกว่งตามปกติ</p>
""" + quiz(
    ("ทำไมบอร์ดจึงมีเซนเซอร์วัดอุณหภูมิสองตัว", "เทียบกันได้ และถ้าสองตัวต่างกันมากแสดงว่าตัวใดตัวหนึ่งอาจเสีย ค่าที่วัดมีความคลาดเคลื่อนเสมอ"),
    ("ความดันอากาศลดลงเร็วๆ บอกอะไร", "มักเป็นสัญญาณว่าอากาศกำลังเปลี่ยน อาจมีฝนหรือพายุ (แต่ไม่ใช่การพยากรณ์ที่แน่นอน)"),
    ("node 4 คือค่าอะไร และหน่วยคืออะไร", "ความชื้นสัมพัทธ์จาก HTS221 หน่วยเป็นเปอร์เซ็นต์ (%)")) + step_nav("0-start.html", "2-board.html"))

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
<div class="warn"><b>ตั้ง <code>TELEGRAM_ALLOWED_CHAT_ID</code> ด้วย</b> ไม่งั้นคนแรกที่ส่ง <code>/start</code> ให้บอทจะกลายเป็นเจ้าของ (หา chat id จาก <code>@userinfobot</code>)<br><b>ระวัง</b> token ของบอทเหมือนรหัสผ่าน อย่าส่งให้ใครหรืออัปโหลดขึ้น GitHub
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
<h2>สนามเล่น: ปรับแล้วดู z เปลี่ยน</h2>
<p>ข้อมูลนี้จำลองในเบราว์เซอร์ ใช้สูตรเดียวกับโค้ดจริง ลองตอบคำถามเหล่านี้โดยเลื่อนแถบ</p>
<div data-play="zscore"></div>
<ol>
<li>ตั้งเหตุการณ์เป็น "กระโดดช่วงท้าย" ลดขนาดการเปลี่ยนแปลงทีละน้อย ถึงขนาดเท่าไหร่ AI จึงหยุดเตือน</li>
<li>เพิ่มความแกว่งปกติเป็น 0.8 แล้วหาขนาดการเปลี่ยนแปลงที่ทำให้เตือนอีกครั้ง สัญญาณรบกวนทำให้จับยากขึ้นอย่างไร</li>
<li>เลือก "ค่อยๆ เพิ่มช้าๆ" ตั้งขนาด 4 °C อุณหภูมิเพิ่มเยอะ แต่ AI เตือนไหม ทำไม</li>
<li>เลือก "ไม่มีอะไรเกิดขึ้น" ลด z_limit เหลือ 1 แล้วกด "สุ่มข้อมูลใหม่" หลายครั้ง เกิดการเตือนผิดบ่อยแค่ไหน</li>
</ol>
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
<h2>เล่นต่อบน Colab (ไม่ต้องติดตั้งอะไร)</h2>
<p>โน้ตบุ๊กนี้ใช้โค้ด <code>detect_anomalies</code> ตัวเดียวกับ gateway รันบน CPU ฟรี ปรับค่าด้วยแถบเลื่อนแล้วดูกราฟ และใส่ข้อมูลจริงของคุณได้</p>
<p>""" + colab_btn("anomaly_playground.ipynb", "เปิดสนามเล่นบน Colab") + """</p>
<h2>ข้อจำกัด</h2>
<p>วิธีนี้เทียบกับ "เมื่อกี้" เท่านั้น ถ้าอุณหภูมิค่อยๆ เพิ่มช้ามากทั้งวันจะไม่เตือน และถ้าช่วงอ้างอิงมีเหตุการณ์ผิดปกติปนอยู่ ค่า std จะบวม ทำให้ตรวจไม่ไว
นี่คือสิ่งที่ AI ทุกแบบมี: ทำงานได้ดีภายใต้สมมติฐานบางอย่าง</p>
""" + quiz(
    ("ถ้า std ของช่วงอ้างอิงเท่ากับ 0 จะเกิดอะไรขึ้นกับ z", "หารด้วยศูนย์ หรือ z ใหญ่มากจนเตือนทุกครั้ง จึงต้องมีค่า std ขั้นต่ำ (MIN_STD)"),
    ("z = 5 หมายความว่าอะไร", "ค่าเฉลี่ยล่าสุดห่างจากค่าปกติ 5 เท่าของความแกว่งปกติ ซึ่งเกิดขึ้นโดยบังเอิญน้อยมาก"),
    ("ทำไมอุณหภูมิที่ค่อยๆ เพิ่มช้าๆ จึงหลุดการตรวจ", "ช่วงอ้างอิงกลืนการเพิ่มนั้นเข้าไปเป็น ‘ค่าปกติ’ แล้ว ทำให้ z ไม่ใหญ่ ต้องใช้วิธีดูแนวโน้มแทน")) + step_nav("4-ui.html", "6-ai-chat.html"))

# ----------------------------------------------------------------------------- lesson 6
page("lessons/6-ai-chat.html", "6 AI แชทบน Colab", """
<p>AI แบบที่สองคือ <b>LLM</b> (โมเดลภาษาขนาดใหญ่) ที่อ่านค่าเซนเซอร์ล่าสุดแล้วตอบคำถามเป็นภาษาไทย
โมเดลใหญ่ต้องใช้การ์ดจอ เราจึงยืม <b>GPU ฟรีของ Google Colab</b> แล้วให้ gateway เรียกผ่านลิงก์</p>

<h2>ลองเล่นก่อน: กฎ กับ LLM ต่างกันอย่างไร</h2>
<p>ช่องนี้ใช้ ‘กฎ’ ตอบ (แบบเดียวกับที่ gateway ใช้ตอนไม่มี LLM) ส่วนด้านล่างคือข้อความที่จะส่งให้ LLM จริง
ลองถามคำถามที่กฎไม่รู้ เช่น “พรุ่งนี้อากาศเป็นยังไง”</p>
<div data-play="chat"></div>

<h2>เปิดใช้ LLM บน Colab ในห้าขั้นตอน</h2>
<p>""" + colab_btn("cucumber_llm.ipynb", "เปิดโน้ตบุ๊ก LLM บน Colab") + """</p>
<ol class="setup">
<li><b>เปิดโน้ตบุ๊ก</b>กดปุ่มด้านบน (ต้องล็อกอินบัญชี Google) ไม่ต้องดาวน์โหลดหรือติดตั้งอะไร</li>
<li><b>เลือก GPU</b>เมนู <b>Runtime → Change runtime type → T4 GPU</b> แล้วกด Save</li>
<li><b>กด Run all</b>เมนู <b>Runtime → Run all</b> เซลล์ติดตั้งใช้เวลา 3–6 นาทีครั้งแรก
 (เซลล์ที่ 3 จะตอบ "ตอนนี้ร้อนไหม" ให้ดูว่าโมเดลใช้ได้)</li>
<li><b>คัดลอกลิงก์</b>เลื่อนไปเซลล์สุดท้าย จะมีข้อความ ✅ พร้อมบรรทัด <code>OLLAMA_URL=...</code> คัดลอกสองบรรทัดนั้น
 แล้ว <b>ปล่อยเซลล์ให้รันค้างไว้ อย่าปิดแท็บ</b></li>
<li><b>บอก gateway</b>วางลงใน <code>gateway/.env</code> แล้วรีสตาร์ท</li>
</ol>
""" + code("# gateway/.env\nOLLAMA_URL=https://xxxx.trycloudflare.com\nOLLAMA_MODEL=qwen2.5:3b") + code("docker compose up -d mqtt_collector") + """
<p>เปิดหน้าเว็บแล้วถามในช่องแชท ใต้คำตอบจะบอกเสมอว่า <b>ตอบโดย LLM</b> หรือ <b>ตอบโดยกฎ</b></p>

<h2>ตรวจว่าเชื่อมสำเร็จ</h2>
<ul class="check">
<li>เซลล์ที่ 3 ใน Colab พิมพ์คำตอบภาษาไทยออกมา</li>
<li><code>curl https://xxxx.trycloudflare.com/api/tags</code> ตอบรายชื่อโมเดล (รันจากเครื่องคุณ)</li>
<li>หน้าเว็บ: ถามแล้วใต้คำตอบขึ้น “ตอบโดย LLM”</li>
<li>ถ้ายังขึ้น “ตอบโดยกฎ” ดูวิธีแก้ที่ <a href="../troubleshooting.html">แก้ปัญหา</a></li>
</ul>

<h2>ทดลอง: ทำให้ AI ดีขึ้น (หรือพังให้ดู)</h2>
<p>ในโน้ตบุ๊กมีเซลล์ <b>ลองเล่น</b> ที่ปรับคำถาม ค่าเซนเซอร์ และ system prompt ได้โดยไม่ต้องแก้โค้ด</p>
<table>
<tr><th>ทดลอง</th><th>สังเกตอะไร</th></tr>
<tr><td>ถาม “พรุ่งนี้ฝนตกไหม” ด้วย system prompt เดิม</td><td>โมเดลยอมรับว่าข้อมูลไม่พอ หรือเดามั่ว</td></tr>
<tr><td>ลบประโยค “ห้ามเดาตัวเลข” ออกแล้วถามซ้ำ</td><td>คำตอบเริ่มมีตัวเลขที่ไม่มีในข้อมูลไหม</td></tr>
<tr><td>ติ๊ก “ตรวจพบความผิดปกติ” แล้วถาม “มีอะไรน่ากังวลไหม”</td><td>โมเดลใช้ผลของ AI ตัวแรก (z-score) ได้ถูกต้องไหม</td></tr>
<tr><td>เปลี่ยนโมเดลเป็น <code>qwen2.5:1.5b</code></td><td>เร็วขึ้นแต่ตอบแย่ลงไหม</td></tr>
<tr><td>ถามภาษาอังกฤษ หรือถามเรื่องไม่เกี่ยวกับอากาศ</td><td>โมเดลอยู่ในกรอบที่ตั้งไว้ไหม</td></tr>
</table>
<div class="try"><b>ไม่อยากใช้ Colab</b> ติดตั้ง Ollama บนเครื่อง (RAM ตั้งแต่ 8 GB) รัน <code>ollama pull qwen2.5:3b</code>
แล้วตั้ง <code>OLLAMA_URL=http://host.docker.internal:11434</code> หรือเว้นว่างไว้ ระบบจะตอบด้วยกฎอัตโนมัติ ไม่พัง</div>

<h2>มันตอบจากอะไร</h2>
<p>gateway ไม่ได้ให้ LLM “เดา” แต่ส่งค่าเซนเซอร์ล่าสุดและผลตรวจผิดปกติไปในคำถามด้วย (ดูกล่อง prompt ในสนามเล่นด้านบน)
พร้อมคำสั่งให้ตอบจากข้อมูลที่ให้เท่านั้น เทคนิคนี้เรียกว่า <b>grounding</b> ช่วยลดการเดามั่ว แต่ไม่ได้กำจัดหมด</p>
<div class="warn"><b>ระวัง</b> ลิงก์ Colab ใครได้ไปก็ใช้โมเดลของคุณได้ อย่าแชร์ต่อ ข้อความแชตผ่านเซิร์ฟเวอร์ของ Google/Cloudflare
อย่าพิมพ์ข้อมูลส่วนตัว และ LLM ตอบผิดได้ อย่าใช้ตัดสินใจเรื่องความปลอดภัย</div>
""" + quiz(
    ("ทำไมต้องส่งค่าเซนเซอร์ไปพร้อมคำถาม แทนที่จะถามโมเดลตรงๆ", "โมเดลไม่รู้ค่าจริงของห้องเรา ถ้าไม่ส่งไปจะเดา การส่งข้อมูลจริงให้ (grounding) ทำให้คำตอบอิงข้อเท็จจริง"),
    ("ทำไมต้องมีกฎสำรองเมื่อ LLM ใช้ไม่ได้", "ระบบต้องไม่พังเมื่อส่วนใดส่วนหนึ่งล่ม Colab ฟรีหยุดเองได้ จึงออกแบบให้ล้มเหลวอย่างปลอดภัย"),
    ("ถ้า LLM บอกว่า ‘ไม่มีความผิดปกติ’ แต่ z-score เตือน ควรเชื่ออะไร", "ผลคำนวณจาก z-score ตรวจสอบย้อนได้ ส่วน LLM อาจตอบผิด จึงควรเชื่อตัวเลขที่คำนวณได้ก่อนแล้วไปดูว่าทำไม LLM ตอบต่าง")) + step_nav("5-ai-anomaly.html", "../challenges.html"))

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
<li>เตรียม <code>devices/simulator.py</code> และ <code>devices/scenario.py</code> ไว้ให้กลุ่มที่บอร์ดไม่พอ (ดู <a href="no-board.html">ไม่มีบอร์ด ใช้ตัวจำลอง</a>)</li>
<li>บทที่ 5 และ 6 มีสนามเล่นในหน้าเว็บและโน้ตบุ๊ก Colab ให้ นักเรียนกดปุ่มเปิดเองได้ ไม่ต้องติดตั้ง</li>
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
<tr><td colspan="2">ตารางปัญหาแบบเต็มอยู่ที่ <a href="troubleshooting.html">แก้ปัญหา</a></td></tr>
<tr><td>AI ตอบ "กฎง่ายๆ" ตลอด</td><td>ลิงก์ Colab หมดอายุหรือยังไม่ได้ใส่ <code>OLLAMA_URL</code></td></tr>
</table>
<h2>ความปลอดภัยและข้อมูลส่วนบุคคล</h2>
<ul>
<li>Mosquitto ในโปรเจกต์เปิดแบบไม่ต้องล็อกอิน (<code>allow_anonymous true</code>) เพื่อให้บอร์ดต่อง่าย เหมาะกับห้องเรียนเท่านั้น อย่าเปิด port 1883 สู่อินเทอร์เน็ต ใครอยู่ WiFi เดียวกันสามารถส่งข้อมูลปลอมเข้ามาได้ gateway จึงรับเฉพาะ node 1–4 และค่าตัวเลขที่ถูกต้อง</li>
<li>API เปิดให้ใครมีลิงก์ก็อ่านได้ (ข้อมูลเป็นสภาพอากาศเท่านั้น) <code>/api/ask</code> จำกัด 12 ครั้ง/นาที ต่อ IP และรวมทั้งระบบไม่เกิน 60 ครั้ง/นาที (ป้องกันการใช้โมเดลถี่เกินไปแบบพื้นฐาน ไม่ใช่การยืนยันตัวตน และ IP จะน่าเชื่อถือเมื่อผ่าน ngrok เท่านั้น) และ CORS อนุญาตเฉพาะ GitHub Pages ของโปรเจกต์ ถ้าเปิดลิงก์ ngrok ให้คนอื่น ให้ปิด ngrok เมื่อเลิกใช้</li>
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

# ----------------------------------------------------------------------------- setup
page("setup.html", "เตรียมเครื่องมือ", """
<p>ทำครั้งเดียว ใช้เวลาประมาณ 15 นาที ทำตามลำดับแล้วติ๊กเช็กลิสต์ท้ายหน้า ถ้าไม่มีบอร์ด ข้ามขั้น PlatformIO ได้</p>
<ol class="setup">
<li><b>Docker Desktop</b>ใช้รัน gateway (Mosquitto + API) ดาวน์โหลดที่ <a href="https://www.docker.com/products/docker-desktop/">docker.com</a>
 เปิดโปรแกรมทิ้งไว้จนไอคอนปลาวาฬนิ่ง ต้องมีพื้นที่ดิสก์ว่างอย่างน้อย 5 GB</li>
<li><b>Python 3.10 ขึ้นไป</b>Mac: <code>brew install python</code> · Windows: ติ๊ก “Add to PATH” ตอนติดตั้งจาก python.org
 แล้วติดตั้งไลบรารีสำหรับตัวจำลอง</li>
</ol>
""" + code("pip install paho-mqtt") + """
<ol class="setup" style="counter-reset:s 2">
<li><b>Git</b>ใช้โหลดโปรเจกต์ (<code>git clone</code>) หรือกดปุ่ม Code → Download ZIP บน GitHub แทนก็ได้</li>
<li><b>PlatformIO</b>(เฉพาะถ้ามีบอร์ด) ติดตั้งส่วนขยาย PlatformIO IDE ใน VS Code หรือรัน <code>pip install platformio</code></li>
<li><b>ngrok</b>(เฉพาะถ้าจะใช้ Telegram) สมัครฟรีที่ ngrok.com แล้วทำตามขั้นตอนติดตั้งและ <code>ngrok config add-authtoken ...</code></li>
<li><b>บัญชี Google</b>สำหรับ Colab ล็อกอินที่ colab.research.google.com ให้เห็นหน้าโน้ตบุ๊กได้ก็พอ</li>
</ol>
<h2>ตรวจความพร้อม (2 นาที)</h2>
""" + code("docker --version\ndocker run --rm hello-world     # ต้องขึ้น Hello from Docker!\npython3 --version\npio --version                    # ถ้ามีบอร์ด\ngit --version") + """
<ul class="check">
<li><code>docker run hello-world</code> สำเร็จ</li>
<li>Python เป็น 3.10 ขึ้นไป และ <code>pip install paho-mqtt</code> ผ่าน</li>
<li>ได้โปรเจกต์มาแล้ว: <code>git clone https://github.com/""" + f"{OWNER}/{NAME}" + """</code></li>
<li>เปิดลิงก์ Colab ในบทที่ 6 ได้ (ล็อกอินแล้ว)</li>
<li>(ถ้ามีบอร์ด) <code>pio --version</code> ทำงาน และเสียบสาย USB แล้วเห็นพอร์ตใหม่</li>
</ul>
<div class="try"><b>เช็กอย่างรวดเร็ว</b> เปิด gateway ทดสอบ <code>cd gateway &amp;&amp; cp .env.example .env &amp;&amp; docker compose up -d --build</code>
แล้วเปิด <a href="http://localhost:5001/app">localhost:5001/app</a> ถ้าเห็นหน้าเว็บ (แม้ยังไม่มีข้อมูล) เครื่องของคุณพร้อมแล้ว</div>
<div class="warn"><b>ติดปัญหา</b> ดู <a href="troubleshooting.html">แก้ปัญหา</a> ก่อน ส่วนใหญ่เป็นเรื่อง Docker ยังไม่พร้อม หรือพอร์ตชน</div>
""")

# ----------------------------------------------------------------------------- applications
page("applications.html", "นำไปประยุกต์ใช้", """
<p>ระบบที่เราสร้างทำสามอย่างต่อกัน: <b>วัดค่า → ตรวจว่าผิดปกติไหม → ให้ถามเป็นภาษาไทยได้</b>
ไม่ได้ผูกกับแตงกวา เปลี่ยนที่ติดตั้งก็ใช้กับเรื่องอื่นได้ ตารางนี้เป็นตัวอย่างความคิด ตัวเลขเป็นเพียงแนวทาง
ก่อนใช้จริงต้องถามผู้รู้ในเรื่องนั้นหรือค้นข้อมูลที่เชื่อถือได้</p>
<h2>ตัวอย่างสถานการณ์</h2>
<table>
<tr><th>ที่ใช้</th><th>วัดอะไร</th><th>ผิดปกติแปลว่า</th><th>แล้วควรทำอะไร</th></tr>
<tr><td><b>โรงเรือนแตงกวา</b> (โจทย์หลักของเรา)</td><td>อุณหภูมิ ความชื้น</td><td>ร้อนจัดหรือชื้นผิดปกติ เสี่ยงต่อพืชและโรคราบางชนิด</td><td>เปิดพัดลม ระบายอากาศ รดน้ำตามความเหมาะสม</td></tr>
<tr><td><b>ห้องเรียน</b></td><td>อุณหภูมิ ความชื้น</td><td>ห้องอบอ้าว นักเรียนเรียนไม่ไหว</td><td>เปิดพัดลม/แอร์ เปิดหน้าต่าง ย้ายกิจกรรม</td></tr>
<tr><td><b>ห้องสมุด/ห้องเก็บเอกสาร</b></td><td>ความชื้น</td><td>ชื้นสูงเป็นเวลานาน หนังสือขึ้นรา</td><td>เปิดเครื่องลดความชื้น ระบายอากาศ</td></tr>
<tr><td><b>ห้องเซิร์ฟเวอร์/ห้องคอมพิวเตอร์</b></td><td>อุณหภูมิ</td><td>เครื่องร้อนผิดปกติ แอร์อาจเสีย</td><td>แจ้งช่างทันที ลดภาระเครื่อง</td></tr>
<tr><td><b>ห้องเก็บของที่ต้องเย็น</b></td><td>อุณหภูมิ</td><td>อุณหภูมิขึ้นเมื่อประตูเปิดค้างหรือเครื่องทำความเย็นมีปัญหา</td><td>ตรวจประตู เครื่องทำความเย็น</td></tr>
<tr><td><b>ตู้เลี้ยงสัตว์เล็ก/ตู้ปลา</b></td><td>อุณหภูมิ</td><td>ฮีตเตอร์เสียหรือห้องร้อนเกิน</td><td>ตรวจอุปกรณ์ ย้ายตู้จากแดด</td></tr>
</table>
<div class="warn"><b>ระบบนี้เป็นเครื่องมือเรียนรู้</b> ไม่ใช่ระบบความปลอดภัยจริง ห้ามใช้ตัดสินใจเรื่องชีวิต ยา อาหาร หรือไฟไหม้
เซนเซอร์มีความคลาดเคลื่อน และ AI ตรวจพลาดได้ ดูข้อจำกัดในบทที่ 5 (ค่าที่ค่อยๆ เพิ่มช้าๆ ตรวจไม่เจอ)</div>
<h2>สิ่งที่เหมือนกันทุกสถานการณ์</h2>
<ol>
<li><b>วัดค่าที่สัมพันธ์กับปัญหา</b> เลือกว่าจะวัดอะไรจากคำถามว่า "ปัญหาที่กลัวคืออะไร"</li>
<li><b>รู้ว่า "ปกติ" คือเท่าไหร่</b> ตัวตรวจผิดปกติเรียนรู้ค่าปกติจากข้อมูลย้อนหลังของที่นั้นเอง จึงไม่ต้องตั้งเลขตายตัว</li>
<li><b>เตือนแล้วต้องมีคนทำอะไรต่อ</b> ถ้าเตือนแล้วไม่มีใครรู้ว่าต้องทำอะไร ระบบก็ไม่มีประโยชน์</li>
</ol>
<h2>แบบฝึก: ออกแบบสถานการณ์ของคุณเอง</h2>
<p>เลือกสถานการณ์หนึ่งข้อ (จากตารางหรือคิดเอง) แล้วตอบคำถามต่อไปนี้ จดไว้ในสมุดหรือไฟล์</p>
<table>
<tr><th>ข้อ</th><th>คำถาม</th><th>เชื่อมกับบท</th></tr>
<tr><td>1</td><td>ปัญหาที่เรากลัวว่าจะเกิดคืออะไร ใครเสียหาย</td><td>โจทย์</td></tr>
<tr><td>2</td><td>ต้องวัดค่าอะไร บอร์ด Cucumber วัดได้ครบไหม ถ้าไม่ครบต้องเพิ่มเซนเซอร์อะไร</td><td>บท 1–2</td></tr>
<tr><td>3</td><td>ที่นั่นอยู่ห่างจาก WiFi ไหม ไฟเลี้ยงบอร์ดทำอย่างไร</td><td>บท 2–3</td></tr>
<tr><td>4</td><td>ใครควรเห็นหน้าจอ ผ่านเว็บหรือ Telegram</td><td>บท 4</td></tr>
<tr><td>5</td><td>เหตุการณ์ผิดปกติหน้าตาเป็นอย่างไร ฉับพลัน (เช่น ประตูเปิดค้าง) หรือค่อยๆ เปลี่ยน (เช่น ฮีตเตอร์เสื่อม) ตัวตรวจ z-score จับแบบไหนได้</td><td>บท 5</td></tr>
<tr><td>6</td><td>เขียนคำถาม 3 ข้อที่เจ้าของอยากถาม AI และข้อมูลที่ AI ต้องรู้เพื่อตอบได้</td><td>บท 6</td></tr>
<tr><td>7</td><td>ถ้าระบบเตือนผิดหรือเตือนไม่ทัน เสียหายแค่ไหน ยอมรับได้หรือไม่</td><td>ความปลอดภัย</td></tr>
</table>
<div class="try"><b>ลองทำจริง</b> ใช้ <code>python3 devices/scenario.py jump</code> จำลองเหตุการณ์ฉับพลัน และ <code>drift</code> จำลองเหตุการณ์ค่อยๆ เปลี่ยน
แล้วดูว่าเหตุการณ์ในสถานการณ์ของคุณตรงกับแบบไหน ระบบจับได้หรือไม่ (ดู <a href="no-board.html">ไม่มีบอร์ด ใช้ตัวจำลอง</a>)</div>
""")

# ----------------------------------------------------------------------------- no board
page("no-board.html", "ไม่มีบอร์ด ใช้ตัวจำลอง", """
<p>ไม่มีบอร์ดก็เรียนได้ครบทุกบท เพราะ gateway ไม่รู้ว่าข้อความมาจากบอร์ดหรือจากโปรแกรม
ขอเพียงส่งรูปแบบ <code>{"node":N,"value":V}</code> เข้า topic <code>/cn466/data</code></p>
<h2>วิธีที่ 1: ส่งค่าเดียว</h2>
""" + code("python3 devices/simulator.py 30 1013 60    # อุณหภูมิ ความดัน ความชื้น") + """
<h2>วิธีที่ 2: จำลองเหตุการณ์ต่อเนื่อง (มีสัญญาณรบกวนเหมือนจริง)</h2>
<p><code>devices/scenario.py</code> ส่งข้อมูล 60 ชุดอย่างต่อเนื่อง เลือกเหตุการณ์ได้สามแบบ</p>
""" + code("""python3 devices/scenario.py normal              # นิ่งๆ ไม่มีอะไรเกิดขึ้น
python3 devices/scenario.py jump                # นิ่ง แล้วอุณหภูมิกระโดด +2 °C ช่วงท้าย (เหมือนเป่าไดร์)
python3 devices/scenario.py drift --jump 4      # อุณหภูมิค่อยๆ เพิ่ม 4 °C ทั้งชั่วโมง""") + """
<table>
<tr><th>คำสั่ง</th><th>ผลที่ควรเห็นใน /api/anomaly</th><th>บทเรียน</th></tr>
<tr><td><code>normal</code></td><td>ปกติ (z ใกล้ 0)</td><td>ค่าที่ไม่เปลี่ยนไม่ควรถูกเตือน</td></tr>
<tr><td><code>jump</code></td><td>ผิดปกติ (z มากกว่า 3)</td><td>เปลี่ยนฉับพลันจับได้ง่าย</td></tr>
<tr><td><code>drift</code></td><td><b>ปกติ</b> ทั้งที่เพิ่ม 4 °C</td><td>ข้อจำกัดของวิธีนี้ (ดูบทที่ 5)</td></tr>
</table>
<p>ตัวเลือกเสริม: <code>--noise 0.5</code> (สัญญาณรบกวน), <code>--count 100</code> (จำนวนชุด), <code>--interval 1</code> (วินาทีต่อชุด), <code>--seed 7</code> (ให้ผลซ้ำได้)</p>
<h2>ดูผล</h2>
""" + code("curl 'localhost:5001/api/anomaly?minutes=60'") + """
<p>หรือเปิด <a href="http://localhost:5001/app">localhost:5001/app</a> ดูป้ายเตือนบนหน้าเว็บ</p>
<h2>ไม่อยากติดตั้งอะไรเลย</h2>
<ul>
<li>บทที่ 1, 5, 6 มี <b>สนามเล่นในหน้าเว็บ</b> ใช้ได้ทันที ไม่ต้องมี Docker หรือบอร์ด</li>
<li>บทที่ 5 มี <b>โน้ตบุ๊ก Colab</b> ที่รันตัวตรวจผิดปกติตัวจริงได้ในเบราว์เซอร์ """ + colab_btn("anomaly_playground.ipynb", "เปิดบน Colab") + """</li>
</ul>
<h2>เมื่อได้บอร์ดจริง</h2>
<p>หยุดตัวจำลอง ทำบทที่ 2 แล้วข้อมูลจริงจะเข้ามาที่ gateway เดิมโดยไม่ต้องแก้อะไร ลองเทียบความแกว่งของค่าจริงกับค่าจำลองว่าต่างกันอย่างไร</p>
""")

# ----------------------------------------------------------------------------- challenges
page("challenges.html", "ปรับแก้และต่อยอด", """
<p>เมื่อทุกบทผ่านแล้ว เลือกโจทย์ที่สนใจ แต่ละข้อบอกระดับและสิ่งที่ต้องแก้ ใช้ AI ช่วยเขียนได้ แต่ต้อง <a href="ai-workflow.html">ตรวจงานของ AI</a> เสมอ</p>
<div class="try"><b>เลือกสถานการณ์ของคุณเอง</b> ก่อนเลือกโจทย์ด้านล่าง ลองใช้แบบฝึกในหน้า <a href="applications.html">นำไปประยุกต์ใช้</a>
กำหนดว่าจะเฝ้าดูอะไร ผิดปกติแปลว่าอะไร แล้วค่อยปรับเกณฑ์ให้เหมาะ</div>
<h2>ระดับ ★ (ปรับค่า ไม่ต้องเขียนโค้ดใหม่)</h2>
<table>
<tr><th>โจทย์</th><th>แก้ที่ไหน</th><th>ตรวจผลอย่างไร</th></tr>
<tr><td>เปลี่ยนให้เตือนไวขึ้น/ช้าลง</td><td><code>z_limit</code> ใน <code>detect_anomalies()</code></td><td>เทสต์ <code>python3 -m pytest -q tests</code> และสนามเล่นบทที่ 5</td></tr>
<tr><td>เปลี่ยนความถี่อ่านค่าจาก 3 วินาที เป็น 10 วินาที</td><td><code>devices/cucumber/src/main.cpp</code></td><td>ดู Serial Monitor</td></tr>
<tr><td>เปลี่ยนโมเดล LLM</td><td><code>OLLAMA_MODEL</code> ใน <code>.env</code></td><td>เทียบคำตอบและความเร็ว</td></tr>
<tr><td>เปลี่ยนคำสั่ง system prompt</td><td><code>llm_answer()</code> ใน <code>ai_helpers.py</code></td><td>ถามคำถามชุดเดิมแล้วเทียบ</td></tr>
</table>
<h2>ระดับ ★★ (เพิ่มความสามารถ)</h2>
<ol>
<li><b>ค่าเกณฑ์ต่อ node</b> ตอนนี้ใช้ z_limit เดียวทุกเซนเซอร์ ให้ความชื้นใช้ 4 อุณหภูมิใช้ 3</li>
<li><b>ตรวจแนวโน้มช้าๆ (drift)</b> ที่บทที่ 5 จับไม่ได้: เทียบค่าเฉลี่ยของ 10 นาทีแรกกับ 10 นาทีหลัง ว่าต่างกันเกินกี่ °C
 ตรวจด้วย <code>python3 devices/scenario.py drift --jump 4</code></li>
<li><b>ป้ายความสบาย</b> เพิ่มการ์ดในหน้าเว็บ บอกว่า “สบาย / ร้อน / ร้อนชื้น” จาก <code>comfort_level()</code></li>
<li><b>ประวัติ 24 ชั่วโมง</b> ให้กราฟเลือกช่วง 1 ชั่วโมง / 6 ชั่วโมง / 24 ชั่วโมงได้ (API รองรับ <code>?minutes=</code> อยู่แล้ว)</li>
</ol>
<h2>ระดับ ★★★ (ท้าทาย)</h2>
<ol>
<li><b>เซนเซอร์ตัวใหม่</b> ต่อเซนเซอร์แสง (LDR) เพิ่ม node 5 ต้องแก้: firmware, <code>NODE_INFO</code> ใน gateway, <code>mqtt_app.py</code> (ตรวจ node ที่ยอมรับ),
 <code>ai_helpers.py</code> และหน้าเว็บ ลองสั่ง AI ให้ไล่รายการที่ต้องแก้ แล้วตรวจว่าครบไหม</li>
<li><b>ถอดแจ้งเตือนไป Telegram</b> เมื่อพบความผิดปกติ ให้บอทส่งข้อความหาเจ้าของ (ต้องตั้ง <code>TELEGRAM_ALLOWED_CHAT_ID</code> ก่อน)</li>
<li><b>ข้อมูลหลายห้อง</b> ให้บอร์ดแต่ละตัวส่งเข้าห้องของตัวเอง (เช่น topic <code>/cn466/room1/data</code>) และให้หน้าเว็บเลือกห้องได้</li>
<li><b>เทียบ AI สองแบบ</b> วัดว่าระหว่างกฎ กับ LLM แบบไหนตอบคำถาม 10 ข้อได้ถูกกว่า สร้างตารางผลแล้วอภิปราย</li>
</ol>
<div class="try"><b>ทำแล้วเก็บหลักฐาน</b> แต่ละโจทย์ให้บันทึก 3 อย่าง: (1) สั่ง AI ว่าอะไร (2) ตรวจอะไรบ้าง ผ่านหรือไม่ (3) อะไรที่ AI ทำผิดแล้วคุณจับได้
 สามข้อนี้คือสิ่งที่ใช้ในคลิปส่งงานได้เลย</div>
""")

# ----------------------------------------------------------------------------- troubleshooting
page("troubleshooting.html", "แก้ปัญหา", """
<p>ตรวจตามลำดับ: <b>บอร์ด → WiFi → MQTT → gateway → หน้าเว็บ → AI</b> ปัญหาส่วนใหญ่อยู่ต้นทาง
เปิด Serial Monitor (<code>pio device monitor</code>) ก่อนเสมอ แล้วดูว่าบอร์ดพิมพ์อะไร</p>
<h2>คำสั่งตรวจสุขภาพระบบ</h2>
""" + code("""docker ps                                   # ต้องเห็น mosquitto กับ mqtt_collector
curl localhost:5001/api/summary             # ต้องได้ JSON (latest ว่างได้ถ้ายังไม่มีข้อมูล)
docker logs gateway-mqtt_collector-1 --tail 30
docker logs gateway-mosquitto-1 --tail 30   # เห็นการเชื่อมต่อของบอร์ดไหม""") + """
<h2>บอร์ดและการอัปโหลด</h2>
<table>
<tr><th>อาการ</th><th>สาเหตุที่พบบ่อย</th><th>วิธีแก้</th></tr>
<tr><td>อัปโหลดไม่ได้ / พอร์ตหาย / Device not configured</td><td>บอร์ดไม่อยู่ในโหมดโหลด หรือสายเป็นสายชาร์จ</td><td>กด BOOT ค้าง แล้วกด RESET หนึ่งครั้ง ปล่อย BOOT แล้วอัปโหลดใหม่ ใช้สายที่ส่งข้อมูลได้ ลองซ้ำอีกรอบ (บางครั้งสำเร็จรอบที่สอง)</td></tr>
<tr><td>Serial Monitor ไม่ขึ้นอะไร</td><td>เลือกพอร์ตผิด หรือยังไม่รีเซ็ตบอร์ดหลังอัปโหลด</td><td>กด RESET หนึ่งครั้ง ตั้ง baud 115200</td></tr>
<tr><td>ค่าเซนเซอร์เป็น 0 หรือ nan</td><td>สาย I2C หลวม</td><td>ตรวจการเสียบเซนเซอร์ แล้ว RESET</td></tr>
</table>
<h2>WiFi และ MQTT</h2>
<table>
<tr><th>อาการ</th><th>สาเหตุที่พบบ่อย</th><th>วิธีแก้</th></tr>
<tr><td>ต่อ WiFi ไม่ได้</td><td>ชื่อ/รหัสผิด หรือเป็น 5 GHz</td><td>ตรวจ <code>secrets.h</code> และใช้ WiFi 2.4 GHz (ใช้ฮอตสปอตมือถือแทนได้)</td></tr>
<tr><td>ต่อ WiFi ได้แต่ MQTT ไม่ผ่าน</td><td>IP ใน <code>Config.h</code> ไม่ใช่ IP ของคอมพิวเตอร์ หรือไฟร์วอลล์บล็อก 1883</td><td>หา IP ใหม่ (<code>ipconfig getifaddr en0</code>) แล้วอัปโหลดซ้ำ และอนุญาตพอร์ต 1883</td></tr>
<tr><td>WiFi โรงเรียนใช้ไม่ได้</td><td>เครือข่ายกันไม่ให้เครื่องคุยกันเอง (client isolation)</td><td>ใช้ฮอตสปอตมือถือ หรือรันตัวจำลองแทนบอร์ด</td></tr>
</table>
<h2>Docker และ gateway</h2>
<table>
<tr><th>อาการ</th><th>สาเหตุที่พบบ่อย</th><th>วิธีแก้</th></tr>
<tr><td><code>docker</code> ค้าง หรือ Cannot connect to the Docker daemon</td><td>Docker Desktop ยังไม่พร้อม หรือดิสก์เต็ม</td><td>เปิด Docker Desktop รอจนพร้อม ถ้ายังไม่หาย รีสตาร์ทและเคลียร์พื้นที่ดิสก์</td></tr>
<tr><td>port is already allocated (5000/1883)</td><td>มีโปรแกรมอื่นใช้พอร์ต (macOS ใช้ 5000)</td><td>เรา map เป็น 5001 อยู่แล้ว ถ้า 1883 ชน ให้ปิด Mosquitto/stack เก่า: <code>docker compose down</code> ของโปรเจกต์เก่า</td></tr>
<tr><td>หน้าเว็บเปิดได้แต่ไม่มีค่า</td><td>ยังไม่มีข้อมูลเข้า</td><td>ดู <code>docker logs gateway-mosquitto-1</code> ว่าบอร์ดต่อเข้ามาไหม หรือรัน <code>simulator.py</code></td></tr>
<tr><td>ส่งข้อมูลแล้ว API ยังเป็นค่าเก่า</td><td>เช็ก node หรือรูปแบบ JSON</td><td>ต้องเป็น <code>{"node":1..4,"value":ตัวเลข}</code> ค่านอกช่วง/ไม่ใช่ตัวเลขจะถูกทิ้ง ดูข้อความใน log</td></tr>
</table>
<h2>Telegram และ ngrok</h2>
<table>
<tr><th>อาการ</th><th>สาเหตุที่พบบ่อย</th><th>วิธีแก้</th></tr>
<tr><td>Mini App เปิดเป็นหน้าเปล่า</td><td><code>MINIAPP_URL</code> ไม่ใช่ https หรือลิงก์ ngrok เปลี่ยนแล้ว</td><td>ngrok ฟรีเปลี่ยนลิงก์ทุกครั้งที่เริ่มใหม่ แก้ <code>.env</code> แล้ว <code>docker compose up -d mqtt_collector</code></td></tr>
<tr><td>ngrok ขึ้นหน้าเตือนก่อนเข้า</td><td>หน้า interstitial ของ ngrok ฟรี</td><td>หน้าเว็บของเราส่ง header ข้ามให้แล้ว เปิดผ่าน Telegram ปกติ</td></tr>
<tr><td>บอทไม่ตอบ</td><td>token ผิด หรือรันบอทสองที่พร้อมกัน</td><td>ตรวจ <code>TELEGRAM_BOT_TOKEN</code> และปิด stack เก่า</td></tr>
</table>
<h2>AI และ Colab</h2>
<table>
<tr><th>อาการ</th><th>สาเหตุที่พบบ่อย</th><th>วิธีแก้</th></tr>
<tr><td>แชตขึ้น “ตอบโดยกฎ” ตลอด</td><td>ยังไม่ได้ใส่ <code>OLLAMA_URL</code> ลิงก์หมดอายุ หรือ Colab หยุดแล้ว</td><td>ดูว่าเซลล์สุดท้ายใน Colab ยังรันอยู่ ถ้าไม่ รันใหม่แล้วคัดลอกลิงก์ใหม่ใส่ <code>.env</code></td></tr>
<tr><td>Colab: เซลล์ติดตั้งนานมาก</td><td>ไม่ได้เลือก GPU หรือโหลดโมเดลครั้งแรก</td><td>Runtime → Change runtime type → T4 GPU ครั้งแรกใช้เวลาหลายนาทีเป็นปกติ</td></tr>
<tr><td>Colab: Address already in use</td><td>รันเซลล์ 2 ซ้ำ</td><td>Runtime → Restart session แล้วรันตั้งแต่ต้น</td></tr>
<tr><td>Colab: ReadTimeout ตอนทดสอบ</td><td>โมเดลยังโหลดไม่เสร็จ หรือใช้ CPU</td><td>รอ 1 นาทีแล้วรันเซลล์ที่ 3 ใหม่ ตรวจว่าเป็น T4</td></tr>
<tr><td>ขึ้นว่าเกินจำนวนครั้ง (429)</td><td>ถูกจำกัดการถาม 12 ครั้งต่อนาทีต่อคน</td><td>รอสักครู่ (ตั้งใจจำกัดเพื่อกันถูกถล่ม)</td></tr>
<tr><td>AI เตือนความผิดปกติผิดๆ</td><td>ข้อมูลอ้างอิงยังน้อย หรือสัญญาณรบกวนมาก</td><td>รอให้มีข้อมูลอย่างน้อย 20 ค่า หรือเพิ่ม <code>z_limit</code></td></tr>
</table>
<div class="try"><b>ยังไม่หาย</b> บันทึก (1) อาการที่เห็น (2) ข้อความใน Serial Monitor / log (3) สิ่งที่ลองแก้แล้ว แล้วถามครูหรือถาม AI พร้อมแนบ 3 อย่างนี้ จะได้คำตอบตรงขึ้นมาก</div>
""")

# ----------------------------------------------------------------------------- security
page("security.html", "ความปลอดภัย", """
<p>ระบบที่ “ทำงานได้” ไม่เท่ากับ “ปลอดภัย” หน้านี้บอกว่าโปรเจกต์นี้ป้องกันอะไรไว้แล้ว และยังเปิดช่องอะไรไว้ตั้งใจ เพื่อให้ห้องเรียนต่อได้ง่าย</p>
<h2>ที่ป้องกันไว้แล้ว</h2>
<table>
<tr><th>เรื่อง</th><th>ทำอย่างไร</th><th>อยู่ที่ไหน</th></tr>
<tr><td>ตรวจข้อมูลขาเข้า</td><td>รับเฉพาะ node 1–4 ค่าเป็นตัวเลขและไม่เกิน 1e9 ข้อมูลแปลกถูกทิ้ง</td><td><code>mqtt_app.py</code></td></tr>
<tr><td>จำกัดการถาม AI</td><td>12 ครั้ง/นาที/คน และ 60 ครั้ง/นาทีรวม</td><td><code>rest_app.py</code></td></tr>
<tr><td>จำกัดเว็บที่เรียก API</td><td>CORS อนุญาตเฉพาะเว็บคอร์สนี้</td><td><code>CORS_ORIGINS</code></td></tr>
<tr><td>ความลับไม่ขึ้น GitHub</td><td><code>.env</code>, <code>secrets.h</code> อยู่ใน <code>.gitignore</code></td><td><code>.gitignore</code></td></tr>
<tr><td>ยืนยันผู้ใช้ Telegram</td><td>ตรวจลายเซ็น HMAC ของ <code>initData</code> ฝั่งเซิร์ฟเวอร์</td><td><code>check_init_data()</code></td></tr>
<tr><td>AI ล่มก็ไม่พัง</td><td>ถอยไปใช้กฎง่ายๆ</td><td><code>answer_question()</code></td></tr>
</table>
<h2>ที่ยังเปิดไว้ (ตั้งใจ)</h2>
<table>
<tr><th>ช่องโหว่</th><th>เสี่ยงอะไร</th><th>ถ้าจะแก้ ต้องเรียนเรื่อง</th></tr>
<tr><td>Mosquitto ไม่ต้องล็อกอิน</td><td>ใครในเครือข่ายเดียวกันส่งค่าปลอมเข้าระบบได้</td><td>username/password, TLS บน MQTT</td></tr>
<tr><td>ข้อมูลเป็น HTTP/MQTT ธรรมดาในห้อง</td><td>ดักอ่านได้ในเครือข่ายเดียวกัน</td><td>TLS / HTTPS</td></tr>
<tr><td>ใครมีลิงก์ ngrok ก็อ่าน API ได้</td><td>เห็นค่าอากาศของห้อง (ไม่มีข้อมูลส่วนตัว)</td><td>การยืนยันตัวตน (authentication)</td></tr>
<tr><td>บอทคนแรกที่ <code>/start</code> เป็นเจ้าของ</td><td>คนแปลกหน้าชิงเป็นเจ้าของบอท</td><td>ตั้ง <code>TELEGRAM_ALLOWED_CHAT_ID</code></td></tr>
<tr><td>ข้อความแชตไปที่ LLM บนอินเทอร์เน็ต</td><td>ข้อมูลส่วนตัวรั่ว และถูกหลอกให้ตอบผิด (prompt injection)</td><td>ความเป็นส่วนตัว การจำกัดสิทธิ์ AI</td></tr>
</table>
<h2>คำถามชวนคิด</h2>
<ol>
<li>ถ้าคุณอยู่ห้องเดียวกัน จะทำให้กราฟของเพื่อนขึ้นว่า “ผิดปกติ” ได้อย่างไร (ตอบด้วยข้อมูลในหน้านี้ ไม่ต้องลองกับระบบของผู้อื่น)</li>
<li>ถ้าระบบนี้สั่งเปิด-ปิดไฟบ้านจริง ช่องโหว่ข้อไหนอันตรายที่สุด</li>
<li>ทำไม AI ในโปรเจกต์นี้ “อ่านค่าและตอบ” เท่านั้น ไม่ได้ “สั่งงานอุปกรณ์”</li>
</ol>
<div class="warn"><b>ข้อตกลง</b> ทดลองเฉพาะกับอุปกรณ์และเครือข่ายของตัวเองหรือที่ได้รับอนุญาตเท่านั้น</div>
""")

# ----------------------------------------------------------------------------- references
page("references.html", "แหล่งอ้างอิง", """
<h2>เครื่องมือและเอกสารที่ใช้</h2>
<table>
<tr><th>หัวข้อ</th><th>ลิงก์</th></tr>
<tr><td>Cucumber R (ESP32-S2)</td><td><a href="https://docs.espressif.com/projects/esp-idf/en/latest/esp32s2/">ESP32-S2 (Espressif)</a></td></tr>
<tr><td>PlatformIO</td><td><a href="https://docs.platformio.org">docs.platformio.org</a></td></tr>
<tr><td>MQTT และ Mosquitto</td><td><a href="https://mosquitto.org">mosquitto.org</a> · <a href="https://mqtt.org">mqtt.org</a></td></tr>
<tr><td>FastAPI</td><td><a href="https://fastapi.tiangolo.com">fastapi.tiangolo.com</a></td></tr>
<tr><td>Docker Compose</td><td><a href="https://docs.docker.com/compose/">docs.docker.com/compose</a></td></tr>
<tr><td>Telegram Mini Apps</td><td><a href="https://core.telegram.org/bots/webapps">core.telegram.org/bots/webapps</a></td></tr>
<tr><td>ngrok</td><td><a href="https://ngrok.com/docs">ngrok.com/docs</a></td></tr>
<tr><td>Ollama</td><td><a href="https://ollama.com">ollama.com</a></td></tr>
<tr><td>Qwen2.5</td><td><a href="https://ollama.com/library/qwen2.5">ollama.com/library/qwen2.5</a></td></tr>
<tr><td>Cloudflare Tunnel (cloudflared)</td><td><a href="https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/">developers.cloudflare.com</a></td></tr>
<tr><td>Google Colab</td><td><a href="https://colab.research.google.com">colab.research.google.com</a></td></tr>
</table>
<h2>แนวคิดสถิติ</h2>
<p>z-score (standard score) คือจำนวนส่วนเบี่ยงเบนมาตรฐานที่ค่าหนึ่งห่างจากค่าเฉลี่ย ดูหัวข้อ “Standard score” ใน Wikipedia</p>
<h2>แรงบันดาลใจ</h2>
<p>รูปแบบหน้า “แก้ปัญหา” และสนามเล่นได้แนวคิดจากเว็บคอร์ส <a href="https://vsupacha.github.io/aiot-for-beginners/">AIoT for Beginners</a>
ซึ่งดัดแปลงจากหลักสูตร <a href="https://github.com/microsoft/IoT-For-Beginners">IoT For Beginners</a> ของ Microsoft (MIT License)
โปรเจกต์นี้เขียนเนื้อหาและโค้ดใหม่ทั้งหมด ไม่ได้คัดลอกเนื้อหามา</p>
<h2>เครื่องมือ AI ที่ใช้พัฒนา</h2>
<p>โปรเจกต์นี้พัฒนาโดยมี Claude Code เป็นผู้ช่วยเขียนโค้ดและเอกสาร ดูวิธีสั่งงานและตรวจงานที่ <a href="ai-workflow.html">ทำงานกับ AI อย่างไร</a></p>
""")

print("built", len(list(DOCS.rglob("*.html"))), "pages")
