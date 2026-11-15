/* Interactive playgrounds for the course pages. Pure JS, no libraries, no network.
   Each widget mirrors the real Python code so what students see here is what the gateway does.
   Mount: <div data-play="sensor|zscore|chat"></div> */
(function () {
  "use strict";

  const $ = (tag, attrs, ...kids) => {
    const el = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs || {})) {
      if (k === "class") el.className = v; else if (k === "text") el.textContent = v;
      else if (k.startsWith("on")) el.addEventListener(k.slice(2), v); else el.setAttribute(k, v);
    }
    kids.flat().forEach(c => el.append(c));
    return el;
  };
  const css = v => getComputedStyle(document.documentElement).getPropertyValue(v).trim() || "#2F6B3F";

  // small seeded RNG so "same seed, same data" can be shown to students
  function rng(seed) {
    let s = seed >>> 0;
    return () => { s = (s + 0x6D2B79F5) >>> 0; let t = s; t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
  }
  function gauss(r) { return Math.sqrt(-2 * Math.log(r() || 1e-9)) * Math.cos(2 * Math.PI * r()); }
  const mean = a => a.reduce((x, y) => x + y, 0) / a.length;
  const pstdev = a => { const m = mean(a); return Math.sqrt(mean(a.map(x => (x - m) ** 2))); };

  function slider(label, min, max, step, value, unit, onInput) {
    const out = $("output", { text: value + " " + unit });
    const input = $("input", { type: "range", min, max, step, value });
    input.addEventListener("input", () => { out.textContent = (+input.value) + " " + unit; onInput(+input.value); });
    return { row: $("label", { class: "sl" }, $("span", { text: label }), input, out), input, out };
  }

  /* ------------------------------------------------------------------ 1) sensor -> message */
  function sensor(root) {
    const st = { t: 29.9, p: 1009.9, h: 60.3 };
    const out = $("pre", { class: "play-out" });
    const note = $("p", { class: "play-note" });
    const draw = () => {
      const t3 = (st.t + 0.5).toFixed(2);
      out.textContent =
        `topic: /cn466/data\n` +
        `{"node":1,"value":${st.t.toFixed(2)}}   <- BMP280 อุณหภูมิ\n` +
        `{"node":2,"value":${st.p.toFixed(2)}}   <- BMP280 ความดัน\n` +
        `{"node":3,"value":${t3}}   <- HTS221 อุณหภูมิ (อ่านต่างจาก BMP280 นิดหน่อย)\n` +
        `{"node":4,"value":${st.h.toFixed(2)}}   <- HTS221 ความชื้น\n\n` +
        `# ส่งเองได้โดยไม่ต้องมีบอร์ด\npython3 devices/simulator.py ${st.t.toFixed(1)} ${st.p.toFixed(0)} ${st.h.toFixed(0)}`;
      const feel = st.t >= 35 ? "ร้อนมาก" : st.t >= 31 ? (st.h >= 70 ? "ร้อนและชื้น อึดอัด" : "ร้อน") : st.t >= 24 ? "สบาย" : "ค่อนข้างเย็น";
      const rain = st.p < 1005 ? "ความดันต่ำ อาจมีฝน" : st.p < 1020 ? "ความดันปกติ" : "ความดันสูง ท้องฟ้าโปร่ง";
      note.textContent = `ตีความ: ${feel} · ${rain}`;
    };
    const a = slider("อุณหภูมิ", 15, 45, 0.1, st.t, "°C", v => { st.t = v; draw(); });
    const b = slider("ความดัน", 980, 1040, 0.5, st.p, "hPa", v => { st.p = v; draw(); });
    const c = slider("ความชื้น", 10, 100, 1, st.h, "%", v => { st.h = v; draw(); });
    root.append($("div", { class: "play-ctl" }, a.row, b.row, c.row), out, note);
    draw();
  }

  /* ------------------------------------------------------------------ 2) z-score */
  function detect(values, zLimit, minStd) {
    const split = Math.max(10, Math.floor(values.length * 0.8));
    const base = values.slice(0, split), recent = values.slice(split);
    const mb = mean(base), sd = Math.max(pstdev(base), minStd);
    const z = (mean(recent) - mb) / sd;
    return { split, mb, sd, rm: mean(recent), z, anomaly: Math.abs(z) > zLimit };
  }

  function zscore(root) {
    const N = 60, BASE = 30.0;
    const st = { noise: 0.2, jump: 1.5, limit: 3, floor: true, mode: "jump", seed: 7 };
    const canvas = $("canvas", { class: "play-canvas", width: 760, height: 280, role: "img",
      "aria-label": "กราฟค่าอุณหภูมิจำลอง 60 จุด" });
    const verdict = $("div", { class: "verdict" });
    const math = $("pre", { class: "play-out" });
    const ctx = canvas.getContext("2d");

    function series() {
      const r = rng(st.seed), s = [];
      const split = Math.floor(N * 0.8);
      for (let i = 0; i < N; i++) {
        let shift = 0;
        if (st.mode === "jump" && i >= split) shift = st.jump;
        if (st.mode === "drift") shift = st.jump * (i / (N - 1));   // slow rise over the whole hour
        s.push(BASE + shift + gauss(r) * st.noise);
      }
      return s;
    }

    function draw() {
      const v = series(), res = detect(v, st.limit, st.floor ? 0.2 : 0);
      const W = canvas.width, H = canvas.height, pad = 34;
      ctx.clearRect(0, 0, W, H);
      const lo = Math.min(...v, res.mb - 3 * res.sd) - 0.3, hi = Math.max(...v, res.mb + 3 * res.sd) + 0.3;
      const X = i => pad + (i / (N - 1)) * (W - pad * 1.5), Y = y => H - pad - ((y - lo) / (hi - lo)) * (H - pad * 1.6);
      const ink = css("--ink"), muted = css("--muted"), green = css("--green"), amber = css("--amber"), line = css("--line");
      // normal band = baseline mean +- z_limit * std
      ctx.fillStyle = green + "22";
      ctx.fillRect(pad, Y(res.mb + st.limit * res.sd), W - pad * 1.5, Y(res.mb - st.limit * res.sd) - Y(res.mb + st.limit * res.sd));
      ctx.strokeStyle = line; ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(pad, H - pad); ctx.lineTo(W - pad / 2, H - pad); ctx.stroke();
      ctx.setLineDash([5, 4]); ctx.strokeStyle = green; ctx.beginPath(); ctx.moveTo(pad, Y(res.mb)); ctx.lineTo(W - pad / 2, Y(res.mb)); ctx.stroke(); ctx.setLineDash([]);
      // split marker
      ctx.strokeStyle = muted; ctx.beginPath(); ctx.moveTo(X(res.split - .5), 8); ctx.lineTo(X(res.split - .5), H - pad); ctx.stroke();
      ctx.fillStyle = muted; ctx.font = "12px IBM Plex Mono, monospace";
      ctx.fillText("อ้างอิง 80%", pad + 4, 16); ctx.fillText("ล่าสุด 20%", X(res.split) + 4, 16);
      ctx.fillText(hi.toFixed(1), 2, 14); ctx.fillText(lo.toFixed(1), 2, H - pad);
      // points
      v.forEach((y, i) => { ctx.fillStyle = i >= res.split ? (res.anomaly ? amber : green) : ink; ctx.beginPath(); ctx.arc(X(i), Y(y), 3.2, 0, 7); ctx.fill(); });
      // recent mean
      ctx.strokeStyle = res.anomaly ? amber : green; ctx.lineWidth = 2.5; ctx.beginPath();
      ctx.moveTo(X(res.split), Y(res.rm)); ctx.lineTo(X(N - 1), Y(res.rm)); ctx.stroke(); ctx.lineWidth = 1;

      verdict.className = "verdict " + (res.anomaly ? "bad" : "ok");
      verdict.textContent = res.anomaly
        ? `⚠ ผิดปกติ  |z| = ${Math.abs(res.z).toFixed(2)} มากกว่า ${st.limit}`
        : `✓ ปกติ  |z| = ${Math.abs(res.z).toFixed(2)} ไม่เกิน ${st.limit}`;
      math.textContent =
        `ค่าเฉลี่ยช่วงอ้างอิง  = ${res.mb.toFixed(2)} °C\n` +
        `std ช่วงอ้างอิง       = ${res.sd.toFixed(3)}${st.floor && res.sd === 0.2 ? "  (ถูกยกขึ้นเป็นค่าต่ำสุด 0.2)" : ""}\n` +
        `ค่าเฉลี่ยช่วงล่าสุด   = ${res.rm.toFixed(2)} °C\n` +
        `z = (${res.rm.toFixed(2)} − ${res.mb.toFixed(2)}) ÷ ${res.sd.toFixed(3)} = ${res.z.toFixed(2)}`;
    }

    const upd = k => v => { st[k] = v; draw(); };
    const s1 = slider("ความแกว่งปกติของเซนเซอร์", 0, 1, 0.01, st.noise, "°C", upd("noise"));
    const s2 = slider("ขนาดการเปลี่ยนแปลง", -5, 5, 0.1, st.jump, "°C", upd("jump"));
    const s3 = slider("เกณฑ์ z_limit", 1, 6, 0.1, st.limit, "", upd("limit"));
    const mode = $("select", { "aria-label": "รูปแบบเหตุการณ์" },
      $("option", { value: "jump", text: "อุณหภูมิกระโดดช่วงท้าย (เช่น เป่าไดร์)" }),
      $("option", { value: "drift", text: "ค่อยๆ เพิ่มช้าๆ ทั้งชั่วโมง" }),
      $("option", { value: "none", text: "ไม่มีอะไรเกิดขึ้น" }));
    mode.addEventListener("change", () => { st.mode = mode.value; draw(); });
    const floor = $("input", { type: "checkbox", checked: "" });
    floor.addEventListener("change", () => { st.floor = floor.checked; draw(); });
    const again = $("button", { class: "btn", type: "button", text: "สุ่มข้อมูลใหม่" });
    again.addEventListener("click", () => { st.seed = (Math.random() * 1e9) | 0; draw(); });

    root.append(
      $("div", { class: "play-ctl" }, s1.row, s2.row, s3.row,
        $("label", { class: "sl" }, $("span", { text: "เหตุการณ์" }), mode),
        $("label", { class: "ck" }, floor, " ใช้ std ขั้นต่ำ 0.2 (MIN_STD) เหมือนโค้ดจริง"), again),
      canvas, verdict, math);
    draw();
  }

  /* ------------------------------------------------------------------ 3) chat: rules vs what the LLM sees */
  const NAMES = { 1: "อุณหภูมิ BMP280", 2: "ความดันอากาศ", 3: "อุณหภูมิ HTS221", 4: "ความชื้น" };
  const UNITS = { 1: "°C", 2: "hPa", 3: "°C", 4: "%" };

  function comfort(t, h) {
    if (t >= 35) return "ร้อนมาก ควรหลีกเลี่ยงกิจกรรมกลางแจ้ง ดื่มน้ำบ่อยๆ";
    if (t >= 31) return "ร้อน" + (h >= 70 ? " และชื้น อึดอัดกว่าปกติ" : "");
    if (t >= 24) return "อุณหภูมิกำลังสบาย";
    return "ค่อนข้างเย็น";
  }
  function ruleAnswer(q, d) {            // port of rule_answer() in ai_helpers.py
    q = q.toLowerCase();
    const has = (...ks) => ks.some(k => q.includes(k));
    if (has("ผิดปกติ", "ผิดสังเกต", "แปลก", "anomaly"))
      return d.anomaly ? "พบความผิดปกติ: อุณหภูมิสูงกว่าปกติ (z=5.2)" : "ตอนนี้ค่าจากเซนเซอร์ยังอยู่ในช่วงปกติ";
    if (has("ความชื้น", "ชื้น", "แห้ง"))
      return `ความชื้นตอนนี้ ${d.h.toFixed(0)}%` + (d.h >= 70 ? " ค่อนข้างชื้น" : d.h >= 40 ? " ปกติ" : " ค่อนข้างแห้ง");
    if (has("ความดัน", "ฝน", "ลม", "hpa"))
      return `ความดันอากาศ ${d.p.toFixed(1)} hPa` + (d.p < 1005 ? " (ต่ำ อาจมีฝน)" : d.p < 1020 ? " (ปกติ)" : " (สูง ท้องฟ้าโปร่ง)");
    return `ตอนนี้อุณหภูมิ ${d.t.toFixed(1)} °C ความชื้น ${d.h.toFixed(0)}% — ` + comfort(d.t, d.h);
  }
  function llmPrompt(q, d) {             // mirrors _context_text() + llm_answer() system prompt
    return "[system]\nคุณคือผู้ช่วยสอนวิทยาศาสตร์สำหรับนักเรียน ม.ปลาย ตอบเป็นภาษาไทย สั้น กระชับ เข้าใจง่าย\n" +
      "ใช้เฉพาะข้อมูลเซนเซอร์ที่ให้มาเท่านั้น ถ้าข้อมูลไม่พอให้บอกตามตรง ห้ามเดาตัวเลข\n\n[user]\nข้อมูลเซนเซอร์ล่าสุด:\n" +
      `- ${NAMES[1]}: ${d.t.toFixed(2)} ${UNITS[1]}\n- ${NAMES[2]}: ${d.p.toFixed(2)} ${UNITS[2]}\n` +
      `- ${NAMES[3]}: ${(d.t + 0.5).toFixed(2)} ${UNITS[3]}\n- ${NAMES[4]}: ${d.h.toFixed(2)} ${UNITS[4]}\n` +
      (d.anomaly ? "- ความผิดปกติที่ตรวจพบ: อุณหภูมิสูงขึ้น (z=5.2)" : "- ยังไม่พบความผิดปกติ") + `\n\nคำถาม: ${q}`;
  }

  function chat(root) {
    const d = { t: 31.5, p: 1008, h: 72, anomaly: false };
    const log = $("div", { class: "chat-log", "aria-live": "polite" });
    const prompt = $("pre", { class: "play-out" });
    const input = $("input", { type: "text", placeholder: "พิมพ์คำถาม เช่น ตอนนี้ร้อนไหม", "aria-label": "คำถาม" });
    const lastQ = { q: "ตอนนี้ร้อนไหม" };
    const showPrompt = () => { prompt.textContent = llmPrompt(lastQ.q, d); };
    function ask(q) {
      q = q.trim(); if (!q) return;
      lastQ.q = q;
      log.append($("div", { class: "msg me", text: q }));
      log.append($("div", { class: "msg bot" }, ruleAnswer(q, d), $("small", { text: "ตอบโดย: กฎ (ไม่มี LLM)" })));
      log.scrollTop = log.scrollHeight; showPrompt();
    }
    const form = $("form", { class: "chat-in" }, input, $("button", { class: "btn solid", text: "ถาม" }));
    form.addEventListener("submit", e => { e.preventDefault(); ask(input.value); input.value = ""; });
    const chips = $("div", { class: "chips" }, ["ตอนนี้ร้อนไหม", "ความชื้นเท่าไหร่", "ฝนจะตกไหม", "มีอะไรผิดปกติไหม", "พรุ่งนี้อากาศเป็นยังไง"]
      .map(q => $("button", { type: "button", class: "chip", text: q, onclick: () => ask(q) })));
    const a = slider("อุณหภูมิ", 15, 45, 0.5, d.t, "°C", v => { d.t = v; showPrompt(); });
    const b = slider("ความดัน", 980, 1040, 1, d.p, "hPa", v => { d.p = v; showPrompt(); });
    const c = slider("ความชื้น", 10, 100, 1, d.h, "%", v => { d.h = v; showPrompt(); });
    const an = $("input", { type: "checkbox" });
    an.addEventListener("change", () => { d.anomaly = an.checked; showPrompt(); });
    root.append(
      $("div", { class: "play-ctl" }, a.row, b.row, c.row, $("label", { class: "ck" }, an, " จำลองว่าตรวจพบความผิดปกติ")),
      chips, log, form,
      $("p", { class: "play-note", text: "ด้านบนคือ ‘กฎ’ ที่ทำงานเมื่อไม่มี LLM ด้านล่างคือข้อความที่ gateway ส่งให้ LLM จริง ลองถาม “พรุ่งนี้อากาศเป็นยังไง” กฎจะตอบไม่ตรงคำถาม แต่ LLM ที่ดีควรบอกว่าข้อมูลไม่พอ" }),
      $("details", { open: "" }, $("summary", { text: "สิ่งที่ LLM เห็น (prompt จริงจาก ai_helpers.py)" }), prompt));
    showPrompt();
  }

  const widgets = { sensor, zscore, chat };
  document.querySelectorAll("[data-play]").forEach(el => {
    const f = widgets[el.dataset.play];
    if (f) { el.classList.add("play"); f(el); }
  });
})();
