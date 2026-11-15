/* Effects for the course site. Vanilla JS, no libraries.
   Ideas adapted from Animmaster's repos: sticky-cards, scroll animation, magnetic marquee,
   pixel page reveal, interactive ASCII. All of it is off when the visitor prefers reduced motion. */
(() => {
  const RM = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const clamp = (v, a, b) => Math.min(b, Math.max(a, v));
  const cssVar = n => getComputedStyle(document.documentElement).getPropertyValue(n).trim();

  /* ---- scroll reveal ---- */
  const targets = $$("main > *:not(.ph):not(.hero):not(.mq):not(.stack)");
  if (RM || !("IntersectionObserver" in window)) {
    targets.forEach(el => el.classList.add("in"));
  } else {
    const io = new IntersectionObserver(es => es.forEach(e => {
      if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); }
    }), { rootMargin: "0px 0px -8% 0px" });
    targets.forEach(el => { el.classList.add("rv"); io.observe(el); });
  }

  /* ---- scroll-linked: progress bar, pipeline, stacking cards ---- */
  const bar = $(".bar"), pipe = $(".pipe"), cards = $$(".lcard");
  const stages = $$(".stage");
  let ticking = false, lastY = scrollY, vel = 0;

  function update() {
    ticking = false;
    const max = document.documentElement.scrollHeight - innerHeight;
    if (bar) bar.style.transform = `scaleX(${max > 0 ? scrollY / max : 0})`;

    if (pipe) {
      const r = pipe.getBoundingClientRect();
      const p = clamp((innerHeight * 0.75 - r.top) / (r.height + innerHeight * 0.1), 0, 1);
      pipe.style.setProperty("--p", p.toFixed(3));
      stages.forEach((s, i) => s.classList.toggle("on", p >= i / (stages.length - 1) - 0.001));
    }

    cards.forEach((card, i) => {
      const next = cards[i + 1];
      if (!next || RM) return;
      const h = card.offsetHeight;
      const gap = next.getBoundingClientRect().top - card.getBoundingClientRect().top;
      const d = clamp((h - gap) / h, 0, 1);
      card.style.transform = `scale(${(1 - 0.04 * d).toFixed(4)})`;
    });
  }
  function onScroll() {
    vel = scrollY - lastY; lastY = scrollY;
    if (!ticking) { ticking = true; requestAnimationFrame(update); }
  }
  addEventListener("scroll", onScroll, { passive: true });
  addEventListener("resize", onScroll);
  update();

  /* ---- marquee: base drift plus scroll velocity ---- */
  const track = $(".mq .track");
  if (track) {
    track.innerHTML += track.innerHTML;
    let x = 0, boost = 0;
    const half = () => track.scrollWidth / 2;
    if (!RM) {
      (function loop() {
        boost += (vel - boost) * 0.08;
        x -= 0.6 + Math.abs(boost) * 0.5;
        const w = half();
        if (-x >= w) x += w;
        track.style.transform = `translate3d(${x}px,0,0)`;
        requestAnimationFrame(loop);
      })();
    }
  }

  /* ---- magnetic buttons ---- */
  if (!RM) {
    $$(".mag").forEach(el => {
      el.addEventListener("pointermove", e => {
        const r = el.getBoundingClientRect();
        const dx = e.clientX - (r.left + r.width / 2), dy = e.clientY - (r.top + r.height / 2);
        el.style.transform = `translate(${clamp(dx * 0.18, -8, 8)}px,${clamp(dy * 0.25, -6, 6)}px)`;
      });
      el.addEventListener("pointerleave", () => { el.style.transform = ""; });
    });
  }

  /* ---- hero: ASCII field, the mouse is the heat source ---- */
  const cv = $("#ascii");
  if (cv) {
    const ctx = cv.getContext("2d");
    const heatOut = $("#heat b");
    const RAMP = " .,:;+*#%@";
    const FS = 15, CW = FS * 0.6, RH = FS * 1.3;
    let W, H, cols, rows, dpr, green, amber, mx = -99, my = -99, heat = 0, target = 0, visible = true;

    const colors = () => { green = cssVar("--green"); amber = cssVar("--amber"); };
    function size() {
      const r = cv.getBoundingClientRect();
      dpr = Math.min(devicePixelRatio || 1, 2);
      W = r.width; H = r.height;
      cv.width = W * dpr; cv.height = H * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.font = `${FS}px "IBM Plex Mono",Menlo,monospace`;
      ctx.textBaseline = "top";
      cols = Math.ceil(W / CW); rows = Math.ceil(H / RH);
    }
    const smooth = (a, b, v) => { const t = clamp((v - a) / (b - a), 0, 1); return t * t * (3 - 2 * t); };

    function draw(t) {
      ctx.clearRect(0, 0, W, H);
      let last = "";
      for (let j = 0; j < rows; j++) {
        for (let i = 0; i < cols; i++) {
          const x = i / cols;
          let v = 0.5 + 0.25 * Math.sin(i * 0.11 + t * 0.0006) + 0.25 * Math.sin(j * 0.17 - t * 0.0004 + i * 0.05);
          v *= smooth(0.3, 0.9, x) * 0.85;
          const dx = (i - mx) * CW, dy = (j - my) * RH;
          const m = Math.exp(-(dx * dx + dy * dy) / (2 * 95 * 95));
          v = Math.min(1, v + m);
          const k = Math.floor(v * (RAMP.length - 1));
          if (k < 1) continue;
          const col = m > 0.3 ? amber : green;
          if (col !== last) { ctx.fillStyle = col; last = col; }
          ctx.globalAlpha = clamp(0.18 + v * 0.62, 0, 0.8);
          ctx.fillText(RAMP[k], i * CW, j * RH);
        }
      }
      ctx.globalAlpha = 1;
    }

    colors(); size();
    matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => { colors(); draw(performance.now()); });
    addEventListener("resize", () => { size(); draw(performance.now()); });

    if (RM) {
      draw(0);
    } else {
      new IntersectionObserver(es => { visible = es[0].isIntersecting; }).observe(cv);
      const hero = cv.parentElement;
      hero.addEventListener("pointermove", e => {
        const r = cv.getBoundingClientRect();
        mx = (e.clientX - r.left) / CW; my = (e.clientY - r.top) / RH; target = 1;
      });
      hero.addEventListener("pointerleave", () => { mx = my = -99; target = 0; });
      let prev = 0;
      (function loop(t) {
        requestAnimationFrame(loop);
        if (!visible || t - prev < 33) return;
        prev = t;
        heat += (target - heat) * 0.12;
        if (heatOut) heatOut.textContent = (29.9 + heat * 6.1).toFixed(1) + " °C";
        draw(t);
      })(0);
    }
  }

  /* ---- page reveal: pixel blocks, first visit per tab only ---- */
  if ($(".hero") && !RM) {
    let seen = false;
    try { seen = sessionStorage.getItem("px") === "1"; sessionStorage.setItem("px", "1"); } catch (e) {}
    if (!seen) {
      const wrap = document.createElement("div");
      wrap.className = "px";
      wrap.setAttribute("aria-hidden", "true");
      const cells = [];
      for (let i = 0; i < 14 * 9; i++) { const c = document.createElement("i"); wrap.appendChild(c); cells.push(c); }
      document.body.appendChild(wrap);
      cells.forEach(c => setTimeout(() => c.classList.add("off"), 150 + Math.random() * 600));
      setTimeout(() => wrap.remove(), 1300);
    }
  }
})();
