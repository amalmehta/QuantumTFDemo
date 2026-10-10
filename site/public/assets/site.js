/* Quantum TF Demo — charts and page behaviour. Data comes from assets/data.js
   (window.QTF_DATA, generated from results/*.json by site/build_site.py).
   Pages opt in with attributes: <svg data-circuit>, <div data-chart="mnist|hybrid|barren|noise">,
   <div data-numbers="...">, <button data-copy>. */
(function () {
  const D = window.QTF_DATA || {};
  const NS = "http://www.w3.org/2000/svg";
  const el = (tag, attrs, parent, text) => {
    const n = document.createElementNS(NS, tag);
    for (const k in attrs) n.setAttribute(k, attrs[k]);
    if (text != null) n.textContent = text;
    if (parent) parent.appendChild(n);
    return n;
  };
  const css = (v) => `var(--${v})`;
  const pct = (x) => (100 * x).toFixed(1) + "%";
  const sup = (n) => String(n).split("").map((c) => "⁰¹²³⁴⁵⁶⁷⁸⁹⁻"["0123456789-".indexOf(c)]).join("");
  const sci = (x) => { const [m, e] = x.toExponential(1).split("e"); return `${m}×10${sup(+e)}`; };
  const mean = (a) => a.reduce((s, x) => s + x, 0) / a.length;
  const std = (a) => { const m = mean(a); return Math.sqrt(mean(a.map((x) => (x - m) ** 2))); };
  const html = (s) => { const t = document.createElement("template"); t.innerHTML = s.trim(); return t.content.firstChild; };

  /* ---------- circuit ---------- */
  function circuit(svg) {
    svg.setAttribute("viewBox", "0 0 760 250");
    const mono = "JetBrains Mono, monospace", sans = "Public Sans, sans-serif";
    const rows = [["q₀", 30], ["q₁", 70], ["q₂", 110], ["⋮", 150], ["q₁₅", 175], ["readout", 225]];
    rows.forEach(([name, y]) => {
      el("text", { x: 4, y: y + 4, fill: css("muted"), "font-family": mono, "font-size": 12 }, svg, name);
      if (name !== "⋮") el("line", { x1: 70, y1: y, x2: 745, y2: y, stroke: css("wire"), "stroke-width": 1.2 }, svg);
    });
    const gate = (x, y, label) => {
      el("rect", { x: x - 15, y: y - 13, width: 30, height: 26, rx: 3, fill: css("gate"), stroke: css("quantum"), "stroke-width": 1.2 }, svg);
      el("text", { x, y: y + 4, "text-anchor": "middle", fill: css("ink"), "font-family": mono, "font-size": 12 }, svg, label);
    };
    const R = 225;
    gate(100, 30, "X"); gate(100, 110, "X");
    el("text", { x: 100, y: 12, "text-anchor": "middle", fill: css("muted"), "font-size": 10, "font-family": sans }, svg, "encode");
    gate(100, R, "X"); gate(140, R, "H");
    const dataY = [30, 70, 110, 175];
    const couple = (x, y, label) => {
      el("line", { x1: x, y1: y, x2: x, y2: R, stroke: css("quantum"), "stroke-width": 1.4 }, svg);
      el("circle", { cx: x, cy: y, r: 4, fill: css("quantum") }, svg);
      el("circle", { cx: x, cy: R, r: 4, fill: css("quantum") }, svg);
      el("text", { x: x + 6, y: (y + R) / 2 + (label === "ZZ" ? 14 : 0), fill: css("quantum"), "font-family": mono, "font-size": 10 }, svg, label);
    };
    let x = 190;
    dataY.forEach((y) => { couple(x, y, "XX"); x += 52; });
    el("text", { x: x - 10, y: 150, fill: css("muted"), "font-size": 16 }, svg, "⋯");
    x += 30;
    dataY.forEach((y) => { couple(x, y, "ZZ"); x += 52; });
    el("text", { x: x - 10, y: 150, fill: css("muted"), "font-size": 16 }, svg, "⋯");
    gate(x + 30, R, "H");
    const mx = x + 80;
    el("rect", { x: mx - 20, y: R - 14, width: 40, height: 28, rx: 3, fill: css("surface"), stroke: css("ink"), "stroke-width": 1.2 }, svg);
    el("text", { x: mx, y: R + 4, "text-anchor": "middle", fill: css("ink"), "font-family": mono, "font-size": 12 }, svg, "⟨Z⟩");
    el("text", { x: 190, y: 12, fill: css("muted"), "font-size": 10, "font-family": sans }, svg, "16 × XX^θᵢ");
    el("text", { x: 190 + 4 * 52 + 30, y: 12, fill: css("muted"), "font-size": 10, "font-family": sans }, svg, "16 × ZZ^φᵢ");
  }

  /* ---------- chart primitives ---------- */
  const M = { l: 46, r: 12, t: 22, b: 34 };
  function frame(parent, title, W = 340, H = 210) {
    const svg = el("svg", { viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": title });
    parent.appendChild(svg);
    el("text", { x: M.l, y: 12, style: "fill:var(--ink)" }, svg, title);
    svg._W = W; svg._H = H;
    return svg;
  }
  function scale(d0, d1, r0, r1, log) {
    if (log) { const a = Math.log10(d0), b = Math.log10(d1); return (v) => r0 + ((Math.log10(v) - a) / (b - a || 1)) * (r1 - r0); }
    return (v) => r0 + ((v - d0) / (d1 - d0 || 1)) * (r1 - r0);
  }
  function axes(svg, xs, ys, xticks, yticks, xfmt, yfmt, xlabel) {
    const W = svg._W, H = svg._H;
    yticks.forEach((t) => {
      el("line", { x1: M.l, x2: W - M.r, y1: ys(t), y2: ys(t), class: "grid" }, svg);
      el("text", { x: M.l - 6, y: ys(t) + 4, "text-anchor": "end" }, svg, yfmt(t));
    });
    xticks.forEach((t) => el("text", { x: xs(t), y: H - M.b + 15, "text-anchor": "middle" }, svg, xfmt(t)));
    el("line", { x1: M.l, x2: W - M.r, y1: H - M.b, y2: H - M.b, class: "axis" }, svg);
    el("text", { x: (M.l + W - M.r) / 2, y: H - 4, "text-anchor": "middle" }, svg, xlabel);
  }
  function series(svg, pts, color, o = {}) {
    const P = (p) => `${o.xs(p[0])},${o.ys(p[1])}`;
    if (o.band) {
      const up = pts.map(([x, y, e]) => [x, y + e]), lo = pts.map(([x, y, e]) => [x, y - e]).reverse();
      el("path", { d: "M" + up.concat(lo).map(P).join("L") + "Z", fill: color, "fill-opacity": 0.14, stroke: "none" }, svg);
    }
    el("path", { class: "line", d: "M" + pts.map(P).join("L"), fill: "none", stroke: color, "stroke-width": o.width || 2,
      "stroke-dasharray": o.dash || "none", "stroke-opacity": o.opacity || 1 }, svg);
    if (o.dots !== false) pts.forEach((p) => {
      if (o.err) el("line", { x1: o.xs(p[0]), x2: o.xs(p[0]), y1: o.ys(p[1] - p[2]), y2: o.ys(p[1] + p[2]), stroke: color, "stroke-width": 1.2 }, svg);
      const c = el("circle", { cx: o.xs(p[0]), cy: o.ys(p[1]), r: 3.4, fill: color }, svg);
      el("title", {}, c, o.tip ? o.tip(p) : `${p[0]}: ${p[1]}`);
    });
  }
  const legendHTML = (items) => `<div class="legend">${items.map(([c, t, faint]) =>
    `<span><i style="background:${c};${faint ? "opacity:.6" : ""}"></i>${t}</span>`).join("")}</div>`;
  function epochStats(runs, key) {
    const arr = runs.map((r) => r.history[key]);
    return arr[0].map((_, i) => { const col = arr.map((a) => a[i]); return [i + 1, mean(col), std(col)]; });
  }

  /* ---------- chart types ---------- */
  function pairChart(box, res, keys, names, showSeeds) {
    const colors = [css("quantum"), css("compare")];
    const grid = document.createElement("div"); grid.className = "pair"; box.appendChild(grid);
    const panels = [["val_loss", "Test hinge loss", (v) => v.toFixed(2)],
                    ["val_hinge_accuracy", "Test accuracy", (v) => (100 * v).toFixed(0) + "%"]];
    panels.forEach(([key, title, fmt]) => {
      const svg = frame(grid, title);
      const stats = keys.map((k) => epochStats(res.runs[k], key));
      const seedVals = keys.flatMap((k) => res.runs[k].flatMap((r) => r.history[key]));
      const all = stats.flat().flatMap(([, m, s]) => [m - s, m + s]).concat(showSeeds ? seedVals : []);
      let lo = Math.min(...all), hi = Math.max(...all);
      const pad = (hi - lo) * 0.1 || 0.05; lo -= pad; hi += pad;
      const n = stats[0].length;
      const xs = scale(1, Math.max(n, 2), M.l + 8, svg._W - M.r - 8), ys = scale(lo, hi, svg._H - M.b, M.t);
      const ticks = [0, 1, 2, 3].map((i) => lo + ((hi - lo) * (i + 0.5)) / 4);
      axes(svg, xs, ys, stats[0].map((p) => p[0]), ticks, (t) => t, fmt, "epoch");
      keys.forEach((k, i) => {
        if (showSeeds) res.runs[k].forEach((r) =>
          series(svg, r.history[key].map((v, j) => [j + 1, v]), colors[i], { xs, ys, width: 1, opacity: 0.45,
            tip: (p) => `${names[i]}, seed ${r.seed}, epoch ${p[0]}: ${fmt(p[1])}` }));
        series(svg, stats[i], colors[i], { xs, ys, band: !showSeeds && stats[i].length > 1,
          tip: (p) => `${names[i]}, epoch ${p[0]}: ${fmt(p[1])} ± ${fmt(p[2])} (mean ± std)` });
      });
    });
    return legendHTML(keys.map((k, i) => [colors[i], names[i]]));
  }

  function barrenChart(box, b) {
    const grid = document.createElement("div"); grid.className = "pair"; box.appendChild(grid);
    const q = b.by_qubits, d = b.by_depth;
    const vs = q.concat(d).map((r) => r.variance);
    const lo = 10 ** Math.floor(Math.log10(Math.min(...vs))), hi = 10 ** Math.ceil(Math.log10(Math.max(...vs)));
    const decades = []; for (let e = Math.log10(lo); e <= Math.log10(hi) + 1e-9; e++) decades.push(10 ** e);
    const dfmt = (t) => "10" + sup(Math.round(Math.log10(t)));
    {
      const svg = frame(grid, `Variance vs qubits (${q[0].depth} layers)`);
      const ns = q.map((r) => r.n_qubits);
      const xs = scale(Math.min(...ns), Math.max(...ns), M.l + 8, svg._W - M.r - 8), ys = scale(lo, hi, svg._H - M.b, M.t, true);
      axes(svg, xs, ys, ns, decades, (t) => t, dfmt, "qubits");
      series(svg, ns.map((n) => [n, Math.exp(b.fit.log_intercept + b.fit.log_slope * n)]), css("fit"), { xs, ys, dash: "5 4", dots: false });
      series(svg, q.map((r) => [r.n_qubits, r.variance]), css("quantum"), { xs, ys, tip: (p) => `${p[0]} qubits: ${sci(p[1])}` });
    }
    {
      const svg = frame(grid, `Variance vs layers (${d[0].n_qubits} qubits)`);
      const ds = d.map((r) => r.depth);
      const xs = scale(Math.min(...ds), Math.max(...ds), M.l + 8, svg._W - M.r - 8, true), ys = scale(lo, hi, svg._H - M.b, M.t, true);
      axes(svg, xs, ys, ds, decades, (t) => t, dfmt, "layers (log scale)");
      series(svg, d.map((r) => [r.depth, r.variance]), css("compare"), { xs, ys, tip: (p) => `${p[0]} layers: ${sci(p[1])}` });
    }
    return legendHTML([[css("quantum"), "measured, by qubits"], [css("fit"), `log-linear fit ∝ ${b.fit.decay_base.toFixed(2)}ⁿ`, true], [css("compare"), "measured, by layers"]]);
  }

  function noiseChart(box, z, showSeeds) {
    const W = 560, H = 250;
    const svg = frame(box, "Test accuracy vs depolarizing noise", W, H);
    const ps = Object.keys(z.summary.eval_only).sort((a, b) => +a - +b);
    const modes = [["eval_only", css("quantum"), "4×4 QNN, trained clean, tested noisy"],
                   ["trained_noisy", css("compare"), `${z.config.size}×${z.config.size} QNN, trained and tested noisy`]];
    const vals = modes.flatMap(([k]) => ps.flatMap((p) => [z.summary[k][p].mean - z.summary[k][p].std, z.summary[k][p].mean + z.summary[k][p].std]))
      .concat(showSeeds ? modes.flatMap(([k]) => ps.flatMap((p) => z.runs[k][p].map((r) => r.test_acc))) : []);
    const lo = Math.max(0, Math.min(...vals) - 0.04), hi = Math.min(1, Math.max(...vals) + 0.04);
    const xs = (v) => M.l + 14 + (ps.indexOf(String(v)) / Math.max(ps.length - 1, 1)) * (W - M.l - M.r - 28);
    const ys = scale(lo, hi, H - M.b, M.t);
    const ticks = [0, 1, 2, 3].map((i) => lo + ((hi - lo) * (i + 0.5)) / 4);
    axes(svg, xs, ys, ps, ticks, (t) => t, (t) => (100 * t).toFixed(0) + "%", "depolarizing probability p per moment (evenly spaced)");
    const chance = ys(0.5);
    if (lo < 0.5) {
      el("line", { x1: M.l, x2: W - M.r, y1: chance, y2: chance, stroke: css("fit"), "stroke-dasharray": "5 4" }, svg);
      el("text", { x: W - M.r, y: chance - 5, "text-anchor": "end" }, svg, "chance");
    }
    modes.forEach(([k, c, name]) => {
      if (showSeeds) ps.forEach((p) => z.runs[k][p].forEach((r) => {
        const dot = el("circle", { cx: xs(p) + (k === "eval_only" ? -5 : 5), cy: ys(r.test_acc), r: 2.2, fill: c, "fill-opacity": 0.5 }, svg);
        el("title", {}, dot, `${name}, p=${p}, seed ${r.seed}: ${pct(r.test_acc)}`);
      }));
      series(svg, ps.map((p) => [p, z.summary[k][p].mean, z.summary[k][p].std]), c,
        { xs, ys, err: !showSeeds, tip: (pt) => `${name}, p=${pt[0]}: ${pct(pt[1])} ± ${pct(pt[2])}` });
    });
    return legendHTML(modes.map(([, c, n]) => [c, n]));
  }

  const CHARTS = {
    mnist: (box, s) => D.mnist_qnn && pairChart(box, D.mnist_qnn, ["qnn", "classical"], ["QNN", "Classical"], s),
    hybrid: (box, s) => D.mnist_qnn && pairChart(box, D.mnist_qnn, ["qnn", "hybrid"], ["Quantum readout", "Hybrid head"], s),
    barren: (box) => D.barren_plateaus && barrenChart(box, D.barren_plateaus),
    noise: (box, s) => D.noise && noiseChart(box, D.noise, s),
  };

  function mountChart(host) {
    const kind = host.dataset.chart, withSeeds = host.hasAttribute("data-seeds");
    let showSeeds = false;
    const draw = () => {
      host.innerHTML = "";
      const body = document.createElement("div"); host.appendChild(body);
      const legend = CHARTS[kind](body, showSeeds);
      if (!legend) { host.innerHTML = '<p class="muted">Results for this experiment are not available yet.</p>'; return; }
      const tools = document.createElement("div"); tools.className = "tools";
      tools.innerHTML = legend;
      if (withSeeds) {
        const id = `seeds-${kind}`;
        const t = html(`<label class="toggle" for="${id}"><input type="checkbox" id="${id}" ${showSeeds ? "checked" : ""}> Show each seed</label>`);
        t.querySelector("input").addEventListener("change", (e) => { showSeeds = e.target.checked; draw(); host.querySelector("input").focus({ preventScroll: true }); });
        tools.appendChild(t);
      }
      host.appendChild(tools);
    };
    draw();
  }

  /* ---------- number panels ---------- */
  const ceil4 = D.data_stats && D.data_stats.by_size.find((r) => r.size === 4);
  const NUMBERS = {
    mnist: () => { const m = D.mnist_qnn; if (!m) return null; const q = m.summary.qnn, c = m.summary.classical; return [
      ["QNN test accuracy", pct(q.mean), `± ${pct(q.std)}`],
      ["Classical test accuracy", pct(c.mean), `± ${pct(c.std)}`],
      ["Parameters", `${m.runs.qnn[0].params} vs ${m.runs.classical[0].params}`],
      ...(ceil4 ? [["Best possible on this input", pct(ceil4.lookup_ceiling), "lookup table"]] : []),
    ]; },
    hybrid: () => { const m = D.mnist_qnn; if (!m || !m.runs.hybrid) return null; const q = m.summary.qnn, h = m.summary.hybrid; return [
      ["Quantum readout", pct(q.mean), `± ${pct(q.std)}`],
      ["Hybrid head", pct(h.mean), `± ${pct(h.std)}`],
      ["Difference", `+${((h.mean - q.mean) * 100).toFixed(1)}`, "points"],
      ["Parameters", `${m.runs.qnn[0].params} vs ${m.runs.hybrid[0].params}`],
    ]; },
    barren: () => { const b = D.barren_plateaus; if (!b) return null; const q = b.by_qubits, q8 = q.find((r) => r.n_qubits === 8) || q[q.length - 1]; return [
      [`Variance at ${q[0].n_qubits} qubits`, sci(q[0].variance)],
      [`Variance at ${q8.n_qubits} qubits`, sci(q8.variance)],
      [`Variance at ${q[q.length - 1].n_qubits} qubits`, sci(q[q.length - 1].variance)],
      ["Random circuits per point", String(b.config.n_circuits)],
    ]; },
    noise: () => { const z = D.noise; if (!z) return null; const ps = Object.keys(z.summary.eval_only).sort((a, b) => +a - +b), p0 = ps[0], pN = ps[ps.length - 1];
      return [
      [`4×4, p = ${p0} → ${pN}`, `${pct(z.summary.eval_only[p0].mean)} → ${pct(z.summary.eval_only[pN].mean)}`],
      [`${z.config.size}×${z.config.size}, p = ${p0} → ${pN}`, `${pct(z.summary.trained_noisy[p0].mean)} → ${pct(z.summary.trained_noisy[pN].mean)}`],
      ["Trajectories per estimate", String(z.config.repetitions)],
    ]; },
  };
  function mountNumbers(host) {
    const rows = NUMBERS[host.dataset.numbers]();
    if (!rows) return;
    host.innerHTML = "<dl>" + rows.map(([t, v, s]) => `<div><dt>${t}</dt><dd>${v}${s ? ` <small>${s}</small>` : ""}</dd></div>`).join("") + "</dl>";
  }

  /* ---------- copy buttons ---------- */
  function mountCopy(btn) {
    btn.addEventListener("click", () => {
      const code = btn.previousElementSibling;
      navigator.clipboard.writeText(code.textContent).then(() => {
        btn.textContent = "Copied"; setTimeout(() => (btn.textContent = "Copy"), 1500);
      }, () => {
        const r = document.createRange(); r.selectNodeContents(code);
        const s = getSelection(); s.removeAllRanges(); s.addRange(r); btn.textContent = "Selected";
      });
    });
  }

  document.querySelectorAll("svg[data-circuit]").forEach(circuit);
  document.querySelectorAll("[data-chart]").forEach(mountChart);
  document.querySelectorAll("[data-numbers]").forEach(mountNumbers);
  document.querySelectorAll("[data-copy]").forEach(mountCopy);
})();
