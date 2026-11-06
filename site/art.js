// One quiet line-art study per disorder. Each <canvas class="art" data-art="..."> runs its own loop.
(function () {
  const INK = "rgba(31, 30, 29, 0.85)";
  const FAINT = "rgba(31, 30, 29, 0.35)";

  const studies = {
    // F67.1 Copium maximum: a breath that keeps being taken.
    copium(ctx, s, t) {
      const c = s / 2;
      for (let i = 0; i < 5; i++) {
        const phase = ((t / 9000) + i / 5) % 1;
        const r = s * 0.06 + phase * s * 0.62;
        ctx.strokeStyle = `rgba(31, 30, 29, ${0.85 * (1 - phase)})`;
        ctx.lineWidth = 1.4;
        ctx.beginPath(); ctx.arc(c, c, r, 0, Math.PI * 2); ctx.stroke();
      }
      ctx.fillStyle = INK;
      ctx.beginPath(); ctx.arc(c, c, 3, 0, Math.PI * 2); ctx.fill();
    },

    // F67.2 Convulsio strategica: each move announced as the direction.
    convulsio(ctx, s, t, st) {
      if (!st.pts) { st.pts = [[s / 2, s / 2]]; st.next = 0; }
      if (t > st.next) {
        const [x, y] = st.pts[st.pts.length - 1];
        const a = Math.random() * Math.PI * 2, d = s * (0.08 + Math.random() * 0.18);
        st.pts.push([Math.min(s * 0.9, Math.max(s * 0.1, x + Math.cos(a) * d)), Math.min(s * 0.9, Math.max(s * 0.1, y + Math.sin(a) * d))]);
        if (st.pts.length > 14) st.pts.shift();
        st.next = t + 380 + Math.random() * 520;
      }
      ctx.lineWidth = 1.4;
      for (let i = 1; i < st.pts.length; i++) {
        ctx.strokeStyle = `rgba(31, 30, 29, ${0.85 * i / st.pts.length})`;
        ctx.beginPath(); ctx.moveTo(...st.pts[i - 1]); ctx.lineTo(...st.pts[i]); ctx.stroke();
      }
      const [x, y] = st.pts[st.pts.length - 1];
      ctx.fillStyle = INK; ctx.beginPath(); ctx.arc(x, y, 3.2, 0, Math.PI * 2); ctx.fill();
    },

    // F67.3 Ave Maria: thrown at the one outcome; arrives short.
    ave(ctx, s, t) {
      const x0 = s * 0.16, y0 = s * 0.78, tx = s * 0.84, ty = s * 0.78;
      ctx.strokeStyle = FAINT; ctx.lineWidth = 1.2;
      ctx.beginPath(); ctx.arc(tx, ty, s * 0.05, 0, Math.PI * 2); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(s * 0.08, y0 + 6); ctx.lineTo(s * 0.92, y0 + 6); ctx.stroke();
      const p = (t % 5200) / 4200;
      if (p > 1) return;
      const reach = 0.86; // never quite the whole way
      const x = x0 + (tx - x0) * reach * p, y = y0 - Math.sin(Math.PI * p) * s * 0.58;
      ctx.strokeStyle = INK; ctx.lineWidth = 1.4; ctx.beginPath();
      for (let q = 0; q <= p; q += 0.01) {
        const qx = x0 + (tx - x0) * reach * q, qy = y0 - Math.sin(Math.PI * q) * s * 0.58;
        q === 0 ? ctx.moveTo(qx, qy) : ctx.lineTo(qx, qy);
      }
      ctx.stroke();
      ctx.fillStyle = INK; ctx.beginPath(); ctx.arc(x, y, 3.4, 0, Math.PI * 2); ctx.fill();
    },

    // F67.4 Delirium incumbentis: two positions held at once, neither centered.
    delirium(ctx, s, t) {
      const c = s / 2, r = s * 0.24;
      const a = t / 2600, b = t / 3700;
      const c1 = [c + Math.cos(a) * s * 0.07, c + Math.sin(a * 1.3) * s * 0.07];
      const c2 = [c + Math.cos(b + 2) * s * 0.11, c + Math.sin(b * 0.7 + 1) * s * 0.11];
      ctx.lineWidth = 1.4;
      ctx.strokeStyle = INK; ctx.beginPath(); ctx.arc(...c1, r, 0, Math.PI * 2); ctx.stroke();
      ctx.strokeStyle = FAINT; ctx.beginPath(); ctx.arc(...c2, r, 0, Math.PI * 2); ctx.stroke();
      const d = [c1[0] + Math.cos(t / 900) * r, c1[1] + Math.sin(t / 900) * r];
      ctx.fillStyle = INK; ctx.beginPath(); ctx.arc(...d, 3.2, 0, Math.PI * 2); ctx.fill();
    },
  };

  document.querySelectorAll("canvas.art").forEach((el) => {
    const study = studies[el.dataset.art] || studies.copium;
    const dpr = window.devicePixelRatio || 1, state = {};
    const size = () => { const s = el.clientWidth; el.width = s * dpr; el.height = s * dpr; return s; };
    let s = size(); window.addEventListener("resize", () => { s = size(); });
    const still = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const frame = (t) => {
      const ctx = el.getContext("2d");
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.clearRect(0, 0, s, s);
      study(ctx, s, t, state);
      if (!still) requestAnimationFrame(frame);
    };
    requestAnimationFrame(frame);
  });
})();
