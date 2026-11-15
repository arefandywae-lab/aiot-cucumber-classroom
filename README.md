# 🥒 AIoT Cucumber Classroom

คอร์ดสอน AIoT สำหรับ **นักเรียนมัธยมปลาย** (ราว 3 ชั่วโมง): ให้บอร์ด **Cucumber R (ESP32-S2)** วัดอุณหภูมิ ความชื้น ความดันอากาศ
ส่งผ่าน MQTT ไปยัง gateway แสดงบนหน้าเว็บหรือ **Telegram Mini App** และมี **AI 2 แบบ** ช่วยตีความข้อมูล

📖 **เว็บคอร์ส (GitHub Pages):** https://arefandywae-lab.github.io/aiot-cucumber-classroom/

```
บอร์ด Cucumber --WiFi/MQTT--> gateway (Docker) --> AI (ตรวจผิดปกติ + LLM บน Colab) --> เว็บ / Telegram
```

| ส่วน | อยู่ที่ | ทำอะไร |
|---|---|---|
| `devices/cucumber/` | PlatformIO / Arduino | อ่าน BMP280 + HTS221 ส่ง MQTT ทุก 3 วินาที |
| `devices/simulator.py` | Python | ส่งข้อมูลจำลองแทนบอร์ด |
| `gateway/` | Docker Compose | Mosquitto + FastAPI + SQLite + หน้าเว็บ/บอท Telegram |
| `gateway/mqtt_collector/ai_helpers.py` | Python | AI #1 z-score ตรวจผิดปกติ, AI #2 แชท (LLM + กฎสำรอง) |
| `ai/colab/cucumber_llm.ipynb` | Colab | รัน LLM (Ollama, Qwen2.5 3B) พร้อมลิงก์สาธารณะ |
| `docs/` | HTML | เว็บคอร์ส 7 บทเรียน + หน้าสำหรับครู (สร้างจาก `tools/build_site.py`) |

## เริ่มเร็ว (ไม่ต้องมีบอร์ด)

```bash
git clone https://github.com/arefandywae-lab/aiot-cucumber-classroom
cd aiot-cucumber-classroom/gateway
cp .env.example .env
docker compose up -d --build
python3 ../devices/simulator.py 30 1013 60     # อุณหภูมิ ความดัน ความชื้น
open http://localhost:5001/app
```

ใช้บอร์ดจริง: ดูบทที่ 2 ในเว็บคอร์ส (ตั้งค่า `Config.h` และ `secrets.h`)

## ตัวเลือก

- **AI:** ตรวจผิดปกติทำงานบนเครื่องเองเสมอ ส่วนแชทใช้ LLM บน Colab หรือ Ollama ในเครื่อง ถ้าไม่ตั้ง `OLLAMA_URL` จะตอบด้วยกฎง่ายๆ
- **UI:** เว็บของโปรเจกต์ (`/app` หรือ `docs/app/?api=URL`) หรือ Telegram (ต้องมี `TELEGRAM_BOT_TOKEN` และ `MINIAPP_URL` แบบ https)

## ทดสอบ

```bash
pip install pytest httpx && python3 -m pytest tests
```

## ความปลอดภัย

`.env` (token) และ `secrets.h` (รหัส WiFi) ถูกกันไว้ใน `.gitignore` Mosquitto เปิดแบบไม่ล็อกอิน ใช้ในห้องเรียนเท่านั้น อย่าเปิด port 1883 สู่อินเทอร์เน็ต

## พัฒนาโดยมี AI ช่วย

ดูวิธีสั่งงานและตรวจงาน AI ในหน้า [ทำงานกับ AI อย่างไร](https://arefandywae-lab.github.io/aiot-cucumber-classroom/ai-workflow.html)

อ้างอิงแนวคิดโครงสร้างคอร์สจาก [aiot-for-beginners](https://vsupacha.github.io/aiot-for-beginners/)
